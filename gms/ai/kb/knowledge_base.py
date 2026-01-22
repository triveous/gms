import frappe
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import VectorStore

_logger = frappe.logger("knowledgbase", allow_site=True, file_count=50)


class KnowledgeBase:
    def __init__(self):
        # Everything is private & lazy
        self._ai_settings = None
        self._ingest_store: VectorStore | None = None
        self._query_store: VectorStore | None = None

    # -------------------------
    # Internal lazy config
    # -------------------------
    def _get_ai_settings(self):
        if self._ai_settings is None:
            _logger.info("Loading AI Settings")
            self._ai_settings = frappe.get_single("AI Settings")
        return self._ai_settings

    def _get_milvus_config(self) -> tuple[str, str | None, str]:
        s = self._get_ai_settings()
        return (
            s.milvus_db_url,
            s.milvus_db_token,
            s.milvus_kb_collection,
        )

    # -------------------------
    # Internal lazy stores
    # -------------------------
    @staticmethod
    def _create_store(
        uri: str,
        token: str | None,
        collection_name: str,
        embedding_model: Embeddings,
        drop_old: bool = False,
    ) -> VectorStore:
        dense_index_param = {"metric_type": "COSINE", "index_type": "HNSW"}
        sparse_index_param = {"metric_type": "BM25", "index_type": "AUTOINDEX"}

        from langchain_milvus import BM25BuiltInFunction, Milvus

        return Milvus(
            auto_id=True,
            embedding_function=embedding_model,
            collection_name=collection_name,
            builtin_function=BM25BuiltInFunction(),
            vector_field=["dense", "sparse"],
            enable_dynamic_field=True,
            connection_args={"uri": uri, "token": token},
            index_params=[dense_index_param, sparse_index_param],
            drop_old=drop_old,
        )

    def _get_ingest_store(self) -> VectorStore:
        if self._ingest_store is None:
            _logger.info("Initializing ingest vector store")
            uri, token, collection = self._get_milvus_config()

            from langchain_google_genai import GoogleGenerativeAIEmbeddings

            ingest_embedding = GoogleGenerativeAIEmbeddings(
                model="gemini-embedding-001",
                task_type="RETRIEVAL_DOCUMENT",
                output_dimensionality=3072,
            )
            self._ingest_store = self._create_store(
                uri,
                token,
                collection,
                ingest_embedding,
            )
        return self._ingest_store

    def _get_query_store(self) -> VectorStore:
        if self._query_store is None:
            _logger.info("Initializing query vector store")
            uri, token, collection = self._get_milvus_config()

            from langchain_google_genai import GoogleGenerativeAIEmbeddings

            query_embedding: Embeddings = GoogleGenerativeAIEmbeddings(
                model="gemini-embedding-001",
                task_type="RETRIEVAL_QUERY",
                output_dimensionality=3072,
            )

            self._query_store = self._create_store(
                uri,
                token,
                collection,
                query_embedding,
            )
        return self._query_store

    # -------------------------
    # Public API (clean)
    # -------------------------
    def add_documents(self, documents: list[Document]):
        return self._get_ingest_store().add_documents(documents)

    def remove_documents(self, expr, filter_params=None):
        filter_params = filter_params or {}
        return self._get_ingest_store().delete(expr=expr, filter_params=filter_params)

    async def retrieve_raw(
        self,
        query: str,
        k: int,
        expr: str | None = None,
    ):
        return await self._get_query_store().asimilarity_search(
            query,
            k=k,
            ranker_type="rrf",
            expr=expr,
            ranker_params={"k": k},
        )
