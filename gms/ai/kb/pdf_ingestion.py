from __future__ import annotations

import hashlib
import json
import os
import re
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO
from typing import Any

import fitz
import frappe
import pymupdf.layout
import pymupdf4llm
from frappe.core.doctype.file.file import File
from google import genai
from google.genai import types as genai_types
from PIL import Image

from gms.ai.kb.kb import Knowledge

VISION_PROMPT = (
    "Analyze this image extracted from a document. "
    "If it contains structured data (table/list), extract it as faithful markdown. "
    "If it is a chart, capture axes, data points, and trend. "
    "If it is a figure/photo, describe factual details. "
    "Always include visible text and numbers accurately."
)

CONTEXT_SYSTEM_INSTRUCTION = (
    "You are a document analysis assistant. "
    "You have the full document as cached context. "
    "For each request, you will receive a single chunk and must return "
    "a short context sentence that improves retrieval quality."
)

DEFAULT_CONTEXT_PROMPT = (
    "Here is the chunk to situate within the full document:\n"
    "<chunk>{{chunk}}</chunk>\n"
    "Return only a concise contextual sentence describing where this chunk fits in the document."
)

INLINE_CONTEXT_TEMPLATE = (
    "<document>{document}</document>\n\n"
    "{prompt}\n"
)


class TokenUsageTracker:
    """Thread-safe token usage tracker for contextualization requests."""

    def __init__(self):
        self.input_tokens = 0
        self.output_tokens = 0
        self.cached_tokens = 0
        self.total_calls = 0
        self._lock = threading.Lock()

    def add_from_response(self, response: Any) -> None:
        usage = getattr(response, "usage_metadata", None)
        if not usage:
            return
        prompt_tokens = int(getattr(usage, "prompt_token_count", 0) or 0)
        output_tokens = int(getattr(usage, "candidates_token_count", 0) or 0)
        cached_tokens = int(getattr(usage, "cached_content_token_count", 0) or 0)
        with self._lock:
            self.input_tokens += prompt_tokens
            self.output_tokens += output_tokens
            self.cached_tokens += cached_tokens
            self.total_calls += 1

    def summary(self) -> str:
        return (
            f"calls={self.total_calls}, input_tokens={self.input_tokens}, "
            f"cached_tokens={self.cached_tokens}, output_tokens={self.output_tokens}"
        )


class PDFIngestionManager:
    def __init__(self):
        self.ai_settings = frappe.get_single("AI Settings")
        self.api_key = os.environ.get("GOOGLE_API_KEY") or frappe.conf.get("google_api_key")
        self.model = self.ai_settings.contextual_chunking_model or "gemini-2.5-flash"
        self.model_config = self._parse_json(self.ai_settings.contextual_chunking_model_config)
        self.context_prompt = (
            self.ai_settings.contextualization_prompt or DEFAULT_CONTEXT_PROMPT
        )
        self.concurrency = max(1, (os.cpu_count() or 1) - 2)

        collection_name = self.ai_settings.milvus_kb_collection or "documents"
        self.kb = Knowledge(
            uri=self.ai_settings.milvus_db_url,
            token=self.ai_settings.milvus_db_token or "",
            collection_name=collection_name,
        )
        self._log(
            f"Initialized with model={self.model}, collection={collection_name}, "
            f"has_api_key={bool(self.api_key)}, concurrency={self.concurrency}"
        )

    @staticmethod
    def _log(message: str) -> None:
        frappe.log(f"[PDFIngestion] {message}")

    @staticmethod
    def _log_error(message: str) -> None:
        frappe.log_error(message, "PDF Ingestion")

    @staticmethod
    def _parse_json(value: str | dict | None) -> dict[str, Any]:
        if not value:
            return {}
        if isinstance(value, dict):
            return value
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        return max(1, len(text) // 4)

    @staticmethod
    def _page_break(line: str) -> int | None:
        stripped = line.strip()
        if stripped in {"-----", "\x0c", "\f"}:
            return -1
        match = re.search(r"<!--\s*Page\s+(\d+)\s*-->", stripped, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return None

    @staticmethod
    def _is_table_line(line: str) -> bool:
        return bool(re.match(r"\s*\|", line))

    @staticmethod
    def _split_text_block(
        text: str, max_tokens: int = 800, overlap_tokens: int = 100
    ) -> list[str]:
        if PDFIngestionManager._estimate_tokens(text) <= max_tokens:
            return [text]

        max_chars = max_tokens * 4
        overlap_chars = overlap_tokens * 4
        chunks: list[str] = []
        paragraphs = re.split(r"\n\s*\n", text)
        current: list[str] = []
        current_len = 0

        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue

            if current_len + len(paragraph) + 1 <= max_chars:
                current.append(paragraph)
                current_len += len(paragraph) + 1
                continue

            if current:
                chunks.append("\n\n".join(current))
                overlap: list[str] = []
                overlap_len = 0
                for part in reversed(current):
                    if overlap_len + len(part) <= overlap_chars:
                        overlap.insert(0, part)
                        overlap_len += len(part)
                    else:
                        break
                current = overlap + [paragraph]
                current_len = sum(len(x) for x in current) + max(len(current) - 1, 0)
                continue

            sentences = re.split(r"(?<=[.!?])\s+", paragraph)
            sent_chunk: list[str] = []
            sent_len = 0
            for sentence in sentences:
                if sent_len + len(sentence) + 1 <= max_chars:
                    sent_chunk.append(sentence)
                    sent_len += len(sentence) + 1
                else:
                    if sent_chunk:
                        chunks.append(" ".join(sent_chunk))
                    sent_chunk = [sentence]
                    sent_len = len(sentence)
            if sent_chunk:
                current = sent_chunk
                current_len = sent_len

        if current:
            chunks.append("\n\n".join(current))

        return chunks

    def parse_pdf_to_elements(self, file_path: str) -> tuple[str, list[dict[str, Any]]]:
        self._log(f"Parsing PDF to markdown: {file_path}")
        markdown_text = pymupdf4llm.to_markdown(file_path)
        lines = markdown_text.split("\n")

        current_page = 1
        current_header = ""
        current_text_block: list[str] = []
        current_table_block: list[str] = []
        in_table = False
        elements: list[dict[str, Any]] = []
        element_order = 0

        def push_text_block():
            nonlocal element_order
            text = "\n".join(current_text_block).strip()
            if text:
                elements.append(
                    {
                        "content": text,
                        "content_type": "text",
                        "page_number": current_page,
                        "section_header": current_header,
                        "element_order": element_order,
                    }
                )
                element_order += 1

        def push_table_block():
            nonlocal element_order
            table_text = "\n".join(current_table_block).strip()
            if table_text:
                elements.append(
                    {
                        "content": table_text,
                        "content_type": "table",
                        "page_number": current_page,
                        "section_header": current_header,
                        "element_order": element_order,
                    }
                )
                element_order += 1

        for line in lines:
            page_marker = self._page_break(line)
            if page_marker is not None:
                if in_table:
                    push_table_block()
                    current_table_block.clear()
                    in_table = False
                if current_text_block:
                    push_text_block()
                    current_text_block.clear()
                if page_marker > 0:
                    current_page = page_marker
                else:
                    current_page += 1
                continue

            heading_match = re.match(r"^#{1,6}\s+(.+)$", line.strip())
            if heading_match:
                current_header = heading_match.group(1).strip()

            is_table = self._is_table_line(line)

            if is_table and not in_table:
                if current_text_block:
                    push_text_block()
                    current_text_block.clear()
                in_table = True
                current_table_block = [line]
                continue

            if is_table and in_table:
                current_table_block.append(line)
                continue

            if not is_table and in_table:
                push_table_block()
                current_table_block.clear()
                in_table = False

            current_text_block.append(line)

        if in_table and current_table_block:
            push_table_block()
        elif current_text_block:
            push_text_block()

        self._log(f"Parsed markdown into {len(elements)} base elements")
        return markdown_text, elements

    @staticmethod
    def extract_images(file_path: str, min_size: int = 100) -> list[dict[str, Any]]:
        images: list[dict[str, Any]] = []
        document = fitz.open(file_path)

        try:
            for page_index in range(len(document)):
                page = document[page_index]
                for image_info in page.get_images(full=True):
                    xref = image_info[0]
                    base_image = document.extract_image(xref)
                    if not base_image:
                        continue

                    image_bytes = base_image.get("image")
                    if not image_bytes:
                        continue

                    width = int(base_image.get("width") or 0)
                    height = int(base_image.get("height") or 0)
                    if width < min_size or height < min_size:
                        continue

                    ext = base_image.get("ext", "png")
                    image_id = hashlib.sha256(image_bytes).hexdigest()[:16]
                    images.append(
                        {
                            "image_id": image_id,
                            "image_bytes": image_bytes,
                            "page_number": page_index + 1,
                            "width": width,
                            "height": height,
                            "ext": ext,
                        }
                    )
        finally:
            document.close()

        frappe.log(f"[PDFIngestion] Extracted {len(images)} images from {file_path}")
        return images

    def _build_generate_config(self, extra: dict[str, Any] | None = None):
        extra = extra or {}
        config_data = dict(self.model_config)
        config_data.update(extra)
        if not config_data:
            return None

        try:
            return genai_types.GenerateContentConfig(**config_data)
        except Exception:
            if extra:
                try:
                    return genai_types.GenerateContentConfig(**extra)
                except Exception:
                    return None
            return None

    def describe_images_parallel(
        self,
        images: list[dict[str, Any]],
        model: str,
        concurrency: int | None = None,
    ) -> list[dict[str, Any]]:
        if concurrency is None:
            concurrency = self.concurrency
        if not images:
            self._log("No images found for vision enrichment")
            return []
        if not self.api_key:
            self._log("GOOGLE_API_KEY missing; skipping image description")
            return []
        self._log(
            f"Running vision enrichment for {len(images)} images "
            f"(model={model}, concurrency={concurrency})"
        )

        client = genai.Client(api_key=self.api_key)

        def describe_one(image_data: dict[str, Any]) -> dict[str, Any] | None:
            try:
                image = Image.open(BytesIO(image_data["image_bytes"]))
                if image.mode not in ("RGB", "RGBA"):
                    image = image.convert("RGB")

                response = client.models.generate_content(
                    model=model,
                    contents=[VISION_PROMPT, image],
                    config=self._build_generate_config(),
                )
                text = (response.text or "").strip()
                if not text:
                    return None

                return {
                    "content": text,
                    "content_type": "image",
                    "page_number": image_data["page_number"],
                    "section_header": "",
                    "image_id": f"{image_data['image_id']}.{image_data['ext']}",
                    "image_width": image_data["width"],
                    "image_height": image_data["height"],
                    "image_ext": image_data["ext"],
                    "element_order": 10_000 + image_data["page_number"],
                }
            except Exception:
                self._log_error("Image description failed\n" + traceback.format_exc())
                return None

        image_elements: list[dict[str, Any]] = []
        with ThreadPoolExecutor(max_workers=max(1, min(concurrency, len(images)))) as pool:
            futures = [pool.submit(describe_one, image_data) for image_data in images]
            for future in as_completed(futures):
                result = future.result()
                if result:
                    image_elements.append(result)

        self._log(f"Generated {len(image_elements)} image description elements")
        return image_elements

    @staticmethod
    def _build_full_text(markdown_text: str, image_elements: list[dict[str, Any]]) -> str:
        if not image_elements:
            return markdown_text

        image_text = "\n\n".join(
            [
                f"[Image on page {element['page_number']}]: {element['content']}"
                for element in image_elements
            ]
        )
        return f"{markdown_text}\n\n--- Image Descriptions ---\n{image_text}".strip()

    def chunk_elements(
        self,
        elements: list[dict[str, Any]],
        chunk_size: int,
        chunk_overlap: int,
    ) -> list[dict[str, Any]]:
        chunks: list[dict[str, Any]] = []
        i = 0

        while i < len(elements):
            element = elements[i]
            content_type = element["content_type"]

            if content_type in {"table", "image"}:
                content = element["content"].strip()
                if not content:
                    i += 1
                    continue

                if element.get("section_header"):
                    content = f"## {element['section_header']}\n\n{content}".strip()

                chunk = {
                    "content": content,
                    "raw_text": content,
                    "content_type": content_type,
                    "page_numbers": [element["page_number"]],
                    "section_header": element.get("section_header") or "",
                    "summary": "",
                    "text_for_sparse": content,
                    "text_for_embedding": content,
                }
                for key in ("image_id", "image_width", "image_height", "image_ext"):
                    if element.get(key):
                        chunk[key] = element[key]
                chunks.append(chunk)
                i += 1
                continue

            text_elements: list[dict[str, Any]] = []
            while i < len(elements) and elements[i]["content_type"] == "text":
                text_elements.append(elements[i])
                i += 1

            merged_text = "\n\n".join(
                [text_element["content"] for text_element in text_elements]
            ).strip()
            if not merged_text:
                continue

            page_numbers = sorted(
                list({text_element["page_number"] for text_element in text_elements})
            )
            section_header = text_elements[0].get("section_header") or ""

            split_text = self._split_text_block(
                merged_text,
                max_tokens=chunk_size,
                overlap_tokens=chunk_overlap,
            )

            for text_chunk in split_text:
                chunks.append(
                    {
                        "content": text_chunk,
                        "raw_text": text_chunk,
                        "content_type": "text",
                        "page_numbers": page_numbers,
                        "section_header": section_header,
                        "summary": "",
                        "text_for_sparse": text_chunk,
                        "text_for_embedding": text_chunk,
                    }
                )

        for idx, chunk in enumerate(chunks):
            chunk["chunk_index"] = idx

        self._log(
            f"Chunking complete: {len(elements)} elements -> {len(chunks)} chunks "
            f"(chunk_size={chunk_size}, overlap={chunk_overlap})"
        )
        return chunks

    def _enrichment_prompt(self, chunk_text: str) -> str:
        if "{{chunk}}" in self.context_prompt:
            return self.context_prompt.replace("{{chunk}}", chunk_text)
        return f"{self.context_prompt}\n\n<chunk>{chunk_text}</chunk>"

    def _build_cache_system_instruction(self) -> str:
        return CONTEXT_SYSTEM_INSTRUCTION

    def _build_cache_enrich_instruction(self) -> str:
        contextual_prompt = self.context_prompt or DEFAULT_CONTEXT_PROMPT
        if "{{chunk}}" in contextual_prompt:
            contextual_prompt = contextual_prompt.replace(
                "{{chunk}}", "<chunk>{chunk}</chunk>"
            )
        return (
            "Instruction for each chunk:\n"
            f"{contextual_prompt}\n"
            "Return only the contextual sentence."
        )

    def _create_context_cache(
        self, client: genai.Client, file_path: str, full_text: str
    ) -> tuple[str | None, str, str | None]:
        system_instruction = self._build_cache_system_instruction()
        enrich_instruction = self._build_cache_enrich_instruction()

        try:
            self._log(f"Uploading source file for context cache: {file_path}")
            uploaded_file = client.files.upload(file=file_path)
            while (
                getattr(uploaded_file, "state", None)
                and uploaded_file.state.name == "PROCESSING"
            ):
                time.sleep(2)
                uploaded_file = client.files.get(name=uploaded_file.name)
            if (
                getattr(uploaded_file, "state", None)
                and uploaded_file.state.name == "FAILED"
            ):
                raise RuntimeError(f"Uploaded file processing failed: {uploaded_file.state}")
            cache = client.caches.create(
                model=self.model,
                config=genai_types.CreateCachedContentConfig(
                    display_name="gms-rag-context",
                    system_instruction=system_instruction,
                    contents=[uploaded_file, enrich_instruction],
                    ttl="1800s",
                ),
            )
            self._log(f"Created context cache from source file: {cache.name}")
            return cache.name, "file", uploaded_file.name
        except Exception:
            self._log_error(
                "File-based context cache creation failed; trying text cache\n"
                + traceback.format_exc()
            )

        try:
            cache = client.caches.create(
                model=self.model,
                config=genai_types.CreateCachedContentConfig(
                    display_name="gms-rag-context",
                    system_instruction=system_instruction,
                    contents=[full_text, enrich_instruction],
                    ttl="1800s",
                ),
            )
            self._log(f"Created context cache from text fallback: {cache.name}")
            return cache.name, "text", None
        except Exception:
            self._log_error(
                "Text-based context cache creation failed; using inline fallback\n"
                + traceback.format_exc()
            )
            return None, "inline", None

    def contextualize_chunks(
        self,
        chunks: list[dict[str, Any]],
        file_path: str,
        full_text: str,
        concurrency: int | None = None,
    ) -> list[dict[str, Any]]:
        if concurrency is None:
            concurrency = self.concurrency
        if not chunks:
            return []

        if not self.api_key:
            self._log("GOOGLE_API_KEY missing; skipping chunk contextualization")
            return chunks

        client = genai.Client(api_key=self.api_key)
        tracker = TokenUsageTracker()
        cache_name, cache_mode, uploaded_file_name = self._create_context_cache(
            client, file_path, full_text
        )
        truncated_document = full_text[:500_000]
        self._log(
            f"Contextualizing {len(chunks)} chunks "
            f"(cache_mode={cache_mode}, concurrency={concurrency})"
        )
        total_chunks = len(chunks)
        completed_chunks = 0
        progress_interval = max(1, total_chunks // 10)
        self._log(f"Contextualization progress: 0/{total_chunks} (0%)")

        def contextualize(idx: int, chunk: dict[str, Any]) -> tuple[int, str]:
            try:
                if cache_name:
                    response = client.models.generate_content(
                        model=self.model,
                        contents=chunk["raw_text"],
                        config=self._build_generate_config(
                            {"cached_content": cache_name}
                        ),
                    )
                else:
                    prompt = self._enrichment_prompt(chunk["raw_text"])
                    response = client.models.generate_content(
                        model=self.model,
                        contents=INLINE_CONTEXT_TEMPLATE.format(
                            document=truncated_document,
                            prompt=prompt,
                        ),
                        config=self._build_generate_config(),
                    )

                tracker.add_from_response(response)
                summary = (response.text or "").strip()
                return idx, summary
            except Exception:
                self._log_error("Chunk contextualization failed for one chunk\n" + traceback.format_exc())
                return idx, ""

        with ThreadPoolExecutor(max_workers=max(1, min(concurrency, len(chunks)))) as pool:
            futures = [
                pool.submit(contextualize, idx, chunk) for idx, chunk in enumerate(chunks)
            ]
            for future in as_completed(futures):
                idx, summary = future.result()
                chunk = chunks[idx]
                chunk["summary"] = summary
                if summary:
                    chunk["text_for_embedding"] = f"{summary}\n\n{chunk['raw_text']}".strip()
                else:
                    chunk["text_for_embedding"] = chunk["raw_text"]

                completed_chunks += 1
                if (
                    completed_chunks == 1
                    or completed_chunks == total_chunks
                    or completed_chunks % progress_interval == 0
                ):
                    percent = int((completed_chunks * 100) / total_chunks)
                    self._log(
                        f"Contextualization progress: {completed_chunks}/{total_chunks} ({percent}%)"
                    )

        if cache_name:
            try:
                client.caches.delete(name=cache_name)
                self._log(f"Deleted context cache: {cache_name}")
            except Exception:
                self._log_error("Context cache deletion failed\n" + traceback.format_exc())

        if uploaded_file_name:
            try:
                client.files.delete(name=uploaded_file_name)
                self._log(f"Deleted uploaded cache file: {uploaded_file_name}")
            except Exception:
                self._log_error("Uploaded cache file deletion failed\n" + traceback.format_exc())

        self._log(f"Contextualization usage summary: {tracker.summary()}")
        self._log("Contextualization completed")

        return chunks

    def _chunks_to_index_documents(
        self,
        chunks: list[dict[str, Any]],
        original_file: File,
        doc_meta: dict[str, Any],
    ) -> list[dict[str, Any]]:
        documents: list[dict[str, Any]] = []

        for chunk in chunks:
            page_numbers = chunk.get("page_numbers") or []
            record: dict[str, Any] = {
                "text": chunk.get("text_for_embedding") or chunk.get("raw_text") or "",
                "raw_text": chunk.get("raw_text", ""),
                "summary": chunk.get("summary", ""),
                "text_for_sparse": chunk.get("text_for_sparse", ""),
                "content_type": chunk.get("content_type", "text"),
                "chunk_index": chunk.get("chunk_index", 0),
                "page_numbers": json.dumps(page_numbers),
                "page_no": page_numbers[0] if page_numbers else None,
                "section_header": chunk.get("section_header", ""),
                "filename": original_file.file_name,
                "mime_type": original_file.file_type,
                **doc_meta,
            }

            for key in ("image_id", "image_width", "image_height", "image_ext"):
                if chunk.get(key) is not None:
                    record[key] = chunk[key]

            documents.append(record)

        return documents

    def delete_existing_chunks(self, ai_document_id: str, file_id: str | None = None) -> None:
        expression = f'ai_document_id == "{ai_document_id}"'
        if file_id:
            expression = f'{expression} or file_id == "{file_id}"'
        self._log(f"Deleting existing chunks with expression: {expression}")
        self.kb.delete_documents_by_expression(expression)

    def ingest_pdf(self, original_file: File, ai_document, doc_meta: dict[str, Any]) -> list[int]:
        file_path = original_file.get_full_path()
        self._log(
            f"Starting ingestion for file={original_file.file_name}, "
            f"ai_document={ai_document.name}, meta_keys={list(doc_meta.keys())}"
        )
        markdown_text, base_elements = self.parse_pdf_to_elements(file_path)

        images = self.extract_images(file_path)
        image_elements = self.describe_images_parallel(
            images=images,
            model=self.model,
            concurrency=self.concurrency,
        )

        elements = base_elements + image_elements
        elements.sort(
            key=lambda element: (
                element.get("page_number", 0),
                element.get("element_order", 0),
            )
        )

        chunk_size = self.ai_settings.chunk_token_size or 1024
        chunk_overlap = 100
        chunks = self.chunk_elements(
            elements,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

        full_text = self._build_full_text(markdown_text, image_elements)
        chunks = self.contextualize_chunks(
            chunks,
            file_path=file_path,
            full_text=full_text,
            concurrency=self.concurrency,
        )

        index_documents = self._chunks_to_index_documents(chunks, original_file, doc_meta)
        inserted_ids = self.kb.index_documents(index_documents)
        self._log(
            f"Indexed {len(index_documents)} chunks into Milvus "
            f"(inserted_ids={len(inserted_ids)}) for ai_document={ai_document.name}"
        )
        return inserted_ids
