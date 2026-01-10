import json
from io import BytesIO

import frappe
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
from langchain_core.document_loaders import BaseLoader
from langchain_core.documents import Document

from gms.ai.kb.knowledge_base import KnowledgeBase
from frappe.core.doctype.file.file import File


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


class DoclingCustomLoader(BaseLoader):
    document: DoclingDocument
    file_name: str
    doc_meta: dict[str, str]
    token_size: int

    def __init__(
        self,
        document: DoclingDocument,
        file_name: str,
        file_mime_type: str,
        doc_meta: dict[str, str] = {},
        token_size: int = 2048,
    ):
        self.document = document
        self.file_name = file_name
        self.file_mime_type = file_mime_type
        self.doc_meta = doc_meta
        self.token_size = token_size

    def lazy_load(self):
        chunks = self._chunking(self.document)
        frappe.log("Chunking done")
        return [self._chunk_to_document(chunk, self.document) for chunk in list(chunks)]

    def _chunk_to_document(
        self, chunk: BaseChunk, document: DoclingDocument
    ) -> Document:
        # noinspection PyTypeChecker
        doc_meta: DocMeta = chunk.meta
        # noinspection PyTypeHints
        page_no = doc_meta.doc_items[0].prov[0].page_no
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
            if ref
        ]

        page_content = f"""\
            {" > ".join(chunk.meta.headings or [])}
            {chunk.text}""".strip()

        return Document(
            page_content=page_content,
            metadata={
                "headings": " <SEP> ".join(chunk.meta.headings or []),
                "page_no": page_no,
                "mime_type": self.file_mime_type,
                "filename": self.file_name,
                "images": json.dumps(images),
                **self.doc_meta,
            },
        )

    def get_stream(self) -> BytesIO:
        if isinstance(self.src, str):
            return BytesIO(open(self.src, "rb").read())
        else:
            return self.src

    @staticmethod
    def _load(src: str | BytesIO, name: str) -> DocumentStream:
        stream = BytesIO(open(src, "rb").read())
        return DocumentStream(name=name, stream=stream)

    def _chunking(self, document: DoclingDocument) -> list[BaseChunk]:
        tokenizer = HuggingFaceTokenizer.from_pretrained(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            max_tokens=self.token_size,
        )
        serializer_provider = MarkdownChunkingSerializerProvider()
        chunker = HybridChunker(
            merge_peers=True,
            tokenizer=tokenizer,
            serializer_provider=serializer_provider,
        )
        return list(chunker.chunk(document))


# Respponsible for ingestion flow
class DoclingIngestionManager:
    kb: KnowledgeBase

    def __init__(self):
        self.kb = KnowledgeBase()

    def request_docling_document(self, original_file: File):
        import base64
        import os

        import requests

        server_url = frappe.get_single_value("GMS Settings", "docling_serve_url")
        # 1. Read the file and encode to base64
        with open(original_file.get_full_path(), "rb") as file:
            encoded_string = base64.b64encode(file.read()).decode("utf-8")

            # 2. Build the JSON payload
        payload = {
            "options": {
                "to_formats": ["json"],  # Specify desired output formats
                "image_export_mode": "placeholder",
                "do_picture_classification": True,
                "do_picture_description": True,
                "abort_on_error": True,
                "picture_description_api": {
                    "concurrency": 2,
                    "headers": {
                        "Authorization": f"Bearer {os.environ.get('GOOGLE_API_KEY')}"
                    },
                    "params": {"model": "gemini-2.0-flash-lite"},
                    "prompt": "Describe this image in a few sentences.",
                    "timeout": 20,
                    "url": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
                },
            },
            "sources": [
                {
                    "kind": "file",
                    "filename": original_file.file_name,
                    "base64_string": encoded_string,
                }
            ],
        }

        # 3. Send the POST request
        headers = {"accept": "application/json", "Content-Type": "application/json"}
        response = requests.post(
            f"{server_url}/v1/convert/source", json=payload, headers=headers
        )
        if response.ok is False:
            print("Docling server error", response.status_code, response.text[:300])
        response.raise_for_status()
        docling_result = response.json()
        docling_dict = docling_result["document"]["json_content"]
        self.process_docling_dict(docling_dict, original_file)

    def process_docling_dict(
        self, docling_dict: dict, original_file: File, doc_meta: dict = dict()
    ):
        document = DoclingDocument.model_validate(docling_dict)
        loader = DoclingCustomLoader(
            document, original_file.file_name, original_file.file_type, doc_meta
        )

        # Support: File Upload

        chunks = list(loader.lazy_load())
        print(f"Generated {len(chunks)} chunks")
        self.kb.add_documents(chunks)
