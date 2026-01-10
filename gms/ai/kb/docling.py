import base64
import json
import os
from io import BytesIO
import asyncio

import frappe
import requests
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
from pydantic_ai import Agent

from gms.ai.kb.knowledge_base import KnowledgeBase


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
    google_api_key: str

    def __init__(self):
        self.google_api_key = os.environ.get("GOOGLE_API_KEY")
        self.kb = KnowledgeBase()

    def get_docling_document_remote(self,original_file:File):
        server_url = frappe.get_single_value("AI Settings", "docling_serve_url")
        
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
                    "headers": {"Authorization": f"Bearer {self.google_api_key}"},
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
        
        return docling_dict
    
    def request_docling_document(self, original_file: File,ai_document:Document):
        if ai_document.transformed_file is None:
            docling_dict = self.get_docling_document_remote(original_file)
            self.save_docling_json(
                docling_dict, original_file, ai_document.name
            )
        else:
            transformed_file = frappe.get_doc("File", ai_document.transformed_file)
            with open(transformed_file.get_full_path(), "r", encoding="utf-8") as f:
                docling_dict = json.load(f)
       
        self.process_docling_dict(docling_dict, original_file)

    def save_docling_json(
        self, docling_dict: dict, original_file: File, ai_document_id: str
    ):
        json_bytes = json.dumps(docling_dict, indent=4).encode("utf-8")
        
        file_doc = frappe.new_doc("File")
        file_doc.file_name = "{original_file.file_name}_docling.json"
        file_doc.content = json_bytes
        
        file_doc.attached_to_doctype = "AI Document"
        file_doc.attached_to_name = ai_document_id
        file_doc.attached_to_field = "transformed_file"
        file_doc.save()
        frappe.db.commit()
        
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

        ChunkContextualizer(
            file_name=original_file.file_name,
            document=document,
            chunks=chunks,
        ).run_sync()
        print("Contextualization done")

        self.kb.add_documents(chunks)


class ChunkContextualizer:
    document: DoclingDocument
    chunks: list[Document]
    api_key: str
    cache_display_name: str

    def __init__(
        self, file_name: str, document: DoclingDocument, chunks: list[Document]
    ):
        self.document = document
        self.chunks = chunks
        self.cache_display_name = file_name
        self.api_key = os.environ.get("GOOGLE_API_KEY")

    def create_cache(self):
        document = self.document.export_to_text()

        URL = "https://generativelanguage.googleapis.com/v1beta/cachedContents"
        headers = {"Content-Type": "application/json", "x-goog-api-key": self.api_key}

        # Define the cache configuration
        data = {
            "model": "models/gemini-2.0-flash",
            "displayName": f"{self.cache_display_name}_cache",
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": f"<document> {document} </document> "}],
                }
            ],
            "ttl": "3600s",
        }

        response = requests.post(URL, headers=headers, data=json.dumps(data))
        cache_info = response.json()

        # The 'name' field is required for Pydantic AI (e.g., 'cachedContents/abcdef123')
        cache_name = cache_info.get("name")
        print(f"Cache created: {cache_name}")
        return cache_name

    def run_sync(self):
        asyncio.run(self.run())
        
    async def run(self):
        cache_name = self.create_cache()
        agent = Agent(
            model="google-gla:gemini-2.0-flash",
            model_settings={"google_cached_content": cache_name},
        )
        
        import asyncio
        frappe.log(f"Using cache: {cache_name}")
        frappe.log(f"Contextualizing {len(self.chunks)} chunks")
        lock = asyncio.Semaphore(5)
        tasks = [asyncio.create_task(self.chunk(idx, agent, chunk, lock)) for idx, chunk in enumerate(self.chunks)]
        results = await asyncio.gather(*tasks)
        
    
    async def chunk(self,idx:int, agent:Agent, chunk: Document,lock: asyncio.Semaphore):
        async with lock:
            frappe.log(f"Contextualizing chunk {idx + 1}")
            result = await agent.run(
                f"""Here is the chunk we want to situate within the whole document <chunk> {chunk.page_content} </chunk> Please give a short succinct context to situate this chunk within the overall document for the purposes of improving search retrieval of the chunk. Answer only with the succinct context and nothing else."""
            )
            chunk.metadata["summary"] = result.output
            chunk.metadata["raw_text"] = chunk.page_content
