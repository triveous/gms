import json
import os
from abc import ABC, abstractmethod
from io import BytesIO
from pathlib import Path

import frappe
from docling.datamodel.document import ConversionResult
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, InputFormat, PdfFormatOption
from docling_core.transforms.chunker import DocMeta, HybridChunker
from docling_core.transforms.chunker.base import BaseChunk
from docling_core.transforms.chunker.hierarchical_chunker import (
    ChunkingDocSerializer,
    ChunkingSerializerProvider,
)
from docling_core.transforms.chunker.tokenizer.huggingface import HuggingFaceTokenizer
from docling_core.transforms.serializer.markdown import (
    MarkdownParams,
    MarkdownTableSerializer,
)
from docling_core.types.doc import DocItemLabel, ImageRefMode
from docling_core.types.doc.document import DoclingDocument, ImageRef
from docling_core.types.io import DocumentStream
from frappe.core.doctype.file.file import File
from langchain_core.document_loaders import BaseLoader
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.vectorstores import VectorStore
from langchain_docling.picture_description import PictureDescriptionLangChainOptions
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_milvus import BM25BuiltInFunction, Milvus
from pydantic import BaseModel, ConfigDict

_logger = frappe.logger("knowledgbase", allow_site=True, file_count=50)


# Transform
PROMPT_PICTURE_DESCRIPTION_DETAILED = """You are a visual analysis expert generating high-fidelity, factual descriptions for the given image

Task:
Analyze the image and produce a detailed, structured description, prioritizing completeness and accuracy.
Describe only what is visible. Do not infer missing information.

⸻

Instructions
	1.	Identify the image type (chart/graph, dashboard, diagram, illustration, photograph, or other).
	2.	If the image conveys data (charts, dashboards, tables, metrics):
	•	Specify the chart type(s)
	•	Describe axes, scales, units, and categories
	•	List all data series, legends, colors, and markers
	•	Describe numerical values or ranges when readable
	•	Explain patterns, trends, comparisons, and notable points
	•	Summarize what the data collectively shows
	3.	If the image is a diagram or illustration:
	•	Explain what it represents
	•	Enumerate components and labels
	•	Describe relationships, flows, and sequences
	•	Note layout and structure
	4.	If any text, values, or visuals are unclear, explicitly say so.

⸻

Output Rules
	•	Be explicit, neutral, and thorough
	•	Prefer structured paragraphs
	•   Be verbose for data-dense images and minimal for simple images.
	•	Do not speculate or add external context
	•	Do not mention the model or prompt

⸻

Goal

Produce a rich, retrieval-optimized image description that fully captures the data and structure for accurate semantic search and downstream reasoning."""

PROMPT_PICTURE_DESCRIPTION_SIMPLE = "Describe this document picture in a few sentences."

CHUNK_SUMMARIZATION_TEMPLATE = """<document>
{{WHOLE_DOCUMENT}}
</document>
Here is the chunk we want to situate within the whole document
<chunk>
{{CHUNK_CONTENT}}
</chunk>
Please give a short succinct context to situate this chunk within the overall document for the purposes of improving search retrieval of the chunk. Answer only with the succinct context and nothing else."""


class MarkdownChunkingSerializerProvider(ChunkingSerializerProvider):
    def get_serializer(self, doc):
        return ChunkingDocSerializer(
            doc=doc,
            table_serializer=MarkdownTableSerializer(),
            params=MarkdownParams(
                image_mode=ImageRefMode.REFERENCED,
                escape_underscores=True,
                escape_html=True,
            ),
        )


class DoclingImageUploader(ABC):
    """
    Base class for uploading assets to a remote storage.
    This will mutate the existing document with ImageRef objects pointing to the uploaded assets.
    """

    def run(self, doc: DoclingDocument):
        for idx, pic in enumerate(doc.pictures):
            if not pic.image:
                continue
            if not self.get_doc_id(doc=doc):
                raise ValueError("Document id is not set.")

            image_name = "_".join(
                [
                    self.get_doc_id(doc=doc),
                    f"{doc.origin.binary_hash:016X}",
                    str(idx + 1),
                    f".{pic.image.pil_image.format.lower() if pic.image.pil_image.format else 'png'}",
                ]
            )

            updated_image = self.save(pic.image, image_name)
            pic.image = updated_image

    @staticmethod
    def get_doc_id(doc: DoclingDocument):
        return doc.name

    @abstractmethod
    def get_prefix(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def save(self, pil: ImageRef, file_name: str) -> ImageRef:
        raise NotImplementedError


class DoclingImageUploaderFrappe(DoclingImageUploader):
    root_dir: str
    folder_created = False

    def __init__(self, root_dir: str):
        super().__init__()
        self.root_dir = root_dir

    def get_prefix(self):
        if not self.folder_created:
            file = frappe.new_doc("File")
            file.is_folder = 1
            if "/" in self.root_dir:
                file.file_name = self.root_dir.split("/")[-1]
                file.folder = "/".join(self.root_dir.split("/")[:-1])
            else:
                file.file_name = self.root_dir
                file.folder = "Home"
            file.insert(ignore_if_duplicate=True)
            self.folder_created = True
        return self.root_dir

    def save(self, image_ref: ImageRef, file_name: str) -> ImageRef:
        pil_image = image_ref.pil_image
        buff = BytesIO()
        pil_image.save(
            buff,
            format=image_ref.mimetype.split("/")[1].upper(),
        )
        file: File = frappe.get_doc(
            {
                "doctype": "File",
                "folder": self.get_prefix(),
                "file_name": file_name,
                "is_private": 1,
                "content": buff.getvalue(),
            }
        ).save(ignore_permissions=True)

        frappe.log(f"File url {file.file_url}")

        return ImageRef(
            mimetype=image_ref.mimetype,
            uri=Path(file.file_url),
            size=image_ref.size,
            dpi=image_ref.dpi,
            _pil=pil_image,
        )


class DoclingCustomLoaderOption(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    image_uploader: DoclingImageUploader
    token_size: int

    enable_picture_description: bool = False
    picture_description_prompt: str = PROMPT_PICTURE_DESCRIPTION_SIMPLE
    picture_description_llm: BaseChatModel | None = None
    images_scale: float = 2.0

    enable_chunk_summary: bool = False
    chunk_summary_prompt: str = CHUNK_SUMMARIZATION_TEMPLATE
    chunk_summary_llm: BaseChatModel | None = None


class DoclingCustomLoader(BaseLoader):
    src: str | BytesIO
    name: str
    option: DoclingCustomLoaderOption
    doc_meta: dict[str, str]

    def __init__(
        self,
        src: str | BytesIO,
        name: str,
        option: DoclingCustomLoaderOption,
        doc_meta: dict[str, str] = {},
    ):
        self.src = src
        self.name = name
        self.option = option
        self.doc_meta = doc_meta

    def lazy_load(self):
        do_stream = self.get_stream()
        frappe.log("Document stream loaded")

        result = self._transform(do_stream)
        frappe.log("Document transformed")

        chunks = self._chunking(result)
        frappe.log("Chunking done")

        return [
            self._chunk_to_document(chunk, result.document) for chunk in list(chunks)
        ]

    def _chunk_to_document(
        self, chunk: BaseChunk, document: DoclingDocument
    ) -> Document:
        # noinspection PyTypeChecker
        doc_meta: DocMeta = chunk.meta
        # noinspection PyTypeHints
        page_no = doc_meta.doc_items[0].prov[0].page_no
        mime_type = doc_meta.origin.mimetype
        binary_hash = str(doc_meta.origin.binary_hash)
        filename = doc_meta.origin.filename

        image_refs: list[ImageRef] = [
            d.get_ref().resolve(document).image
            for d in doc_meta.doc_items
            if d.label == DocItemLabel.PICTURE
        ]
        images = [
            {
                "mime_type": ref.mimetype,
                "uri": str(ref.uri),
                "width": ref.size.width,
                "height": ref.size.height,
                "dpi": ref.dpi,
            }
            for ref in image_refs
        ]

        page_content = f"""\
            {" > ".join(chunk.meta.headings or [])}
            {chunk.text}""".strip()

        return Document(
            page_content=page_content,
            metadata={
                "headings": " <SEP> ".join(chunk.meta.headings or []),
                "page_no": page_no,
                "mime_type": mime_type,
                "binary_hash": binary_hash,
                "filename": filename,
                "images": json.dumps(images),
                **self.doc_meta,
            },
        )

    def get_stream(self) -> DocumentStream:
        if isinstance(self.src, str):
            stream = BytesIO(open(self.src, "rb").read())
        else:
            stream = self.src

        # Load the stream in DocumentStream for transformation
        return DocumentStream(name=self.name, stream=stream)

    @staticmethod
    def _load(src: str | BytesIO, name: str) -> DocumentStream:
        stream = BytesIO(open(src, "rb").read())
        return DocumentStream(name=name, stream=stream)

    def _prepare_pipeline_option(self):
        pdf_pipeline_options = PdfPipelineOptions()
        pdf_pipeline_options.images_scale = self.option.images_scale
        if self.option.enable_picture_description:
            if self.option.picture_description_llm is None:
                assert False, (
                    "picture_description_llm must be provided when enable_picture_description is True"
                )
            pdf_pipeline_options.enable_remote_services = True
            pdf_pipeline_options.allow_external_plugins = True
            pdf_pipeline_options.do_picture_description = True
            pdf_pipeline_options.picture_description_options = (
                PictureDescriptionLangChainOptions(
                    prompt=self.option.picture_description_prompt,
                    llm=self.option.picture_description_llm,
                )
            )
        pdf_pipeline_options.generate_page_images = True  # Allows Tablet Image Gen
        pdf_pipeline_options.generate_picture_images = True
        pdf_pipeline_options.do_table_structure = True
        pdf_pipeline_options.table_structure_options.do_cell_matching = True
        return pdf_pipeline_options

    def _transform(self, source: DocumentStream) -> ConversionResult:
        pipeline_options = self._prepare_pipeline_option()
        converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )
        result = converter.convert(source)

        if self.option.image_uploader is not None:
            self.option.image_uploader.run(result.document)
            frappe.log("Images uploaded")
        return result

    def _chunking(self, result: ConversionResult) -> list[BaseChunk]:
        tokenizer = HuggingFaceTokenizer.from_pretrained(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            max_tokens=self.option.token_size,
        )
        serializer_provider = MarkdownChunkingSerializerProvider()
        chunker = HybridChunker(
            merge_peers=True,
            tokenizer=tokenizer,
            serializer_provider=serializer_provider,
        )
        return list(chunker.chunk(result.document))


class KnowledgeBase:
    ingest_embedding: Embeddings = GoogleGenerativeAIEmbeddings(
        model="gemini-embedding-001", task_type="RETRIEVAL_DOCUMENT"
    )
    query_embedding: Embeddings = GoogleGenerativeAIEmbeddings(
        model="gemini-embedding-001", task_type="RETRIEVAL_QUERY"
    )
    uploader = DoclingImageUploader
    ingest_store: VectorStore
    query_store: VectorStore

    def __init__(
        self,
        name: str = "documents",
        root_path="Home",
        MILVUS_CONN_URI=frappe.conf.get("milvus_conn_uri")
        or os.environ["MILVUS_CONN_URI"],
    ):
        self.ingest_store = self._create_store(
            MILVUS_CONN_URI, name, self.ingest_embedding
        )
        self.query_store = self._create_store(
            MILVUS_CONN_URI, name, self.query_embedding
        )
        self.uploader = DoclingImageUploaderFrappe(root_path)

    @staticmethod
    def _create_store(
        uri: str,
        collection_name: str,
        embedding_model: Embeddings,
        drop_old=False,
    ):
        dense_index_param = {"metric_type": "COSINE", "index_type": "HNSW"}
        sparse_index_param = {"metric_type": "BM25", "index_type": "AUTOINDEX"}
        return Milvus(
            auto_id=True,
            embedding_function=embedding_model,
            collection_name=collection_name,
            builtin_function=BM25BuiltInFunction(),
            vector_field=["dense", "sparse"],
            enable_dynamic_field=True,
            connection_args={"uri": uri},
            index_params=[dense_index_param, sparse_index_param],
            drop_old=drop_old,
        )

    def ingest(self, src: str | BytesIO, name: str, doc_meta: dict = dict()):
        # Load and Chunk
        loader = DoclingCustomLoader(
            src=src,
            name=name,
            option=DoclingCustomLoaderOption(
                image_uploader=self.uploader,
                enable_picture_description=True,
                picture_description_llm=ChatGoogleGenerativeAI(
                    model="gemini-2.0-flash-lite"
                ),
                picture_description_prompt=PROMPT_PICTURE_DESCRIPTION_DETAILED,
                token_size=2048,
                enable_chunk_summary=False,
                chunk_summary_llm=ChatGoogleGenerativeAI(model="gemini-2.0-flash-lite"),
            ),
            doc_meta=doc_meta,
        )
        documents = list(loader.lazy_load())
        self.ingest_store.add_documents(documents)

    def remove(self, expr, filter_params={}):
        return self.ingest_store.delete(expr=expr, filter_params=filter_params)

    def retrieve_raw(
        self,
        query: str,
        k=20,
        rrf_ranker_param: (float, float) = (0.7, 0.3),
        expr: str = None,
    ):
        results = self.query_store.similarity_search(
            query,
            k=k,
            ranker_type="rrf",
            expr=expr,
            # Check params: https://milvus.io/docs/multi-vector-search.md
            ranker_params={"weights": list(rrf_ranker_param)},
        )
        return results

    def load_content():
        pass
