import os

import frappe
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import VectorStore
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_milvus import BM25BuiltInFunction, Milvus

_logger = frappe.logger("knowledgbase", allow_site=True, file_count=50)


class KnowledgeBase:
    ingest_embedding: Embeddings = GoogleGenerativeAIEmbeddings(
        model="gemini-embedding-001",
        task_type="RETRIEVAL_DOCUMENT",
        output_dimensionality=3072,
    )
    query_embedding: Embeddings = GoogleGenerativeAIEmbeddings(
        model="gemini-embedding-001",
        task_type="RETRIEVAL_QUERY",
        output_dimensionality=3072,
    )
    _ingest_store: VectorStore
    _query_store: VectorStore

    def __init__(self):
        ai_settings = frappe.get_single("AI Settings")
        milvus_url = ai_settings.milvus_db_url
        milvus_token = ai_settings.milvus_db_token
        milvus_kb_collection = ai_settings.milvus_kb_collection

        self._ingest_store = self._create_store(
            milvus_url, milvus_token, milvus_kb_collection, self.ingest_embedding
        )
        self._query_store = self._create_store(
            milvus_url, milvus_token, milvus_kb_collection, self.query_embedding
        )

    @staticmethod
    def _create_store(
        uri: str,
        token: str | None,
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
            connection_args={"uri": uri, "token": token},
            index_params=[dense_index_param, sparse_index_param],
            drop_old=drop_old,
        )

    def add_documents(self, documents: list[Document]):
        self._ingest_store.add_documents(documents)

    def remove_documents(self, expr, filter_params={}):
        return self._ingest_store.delete(expr=expr, filter_params=filter_params)

    def retrieve_raw(
        self,
        query: str,
        k: int,
        expr: str = None,
    ):
        results = self._query_store.similarity_search(
            query,
            k=k,
            ranker_type="rrf",
            expr=expr,
            # Check params: https://milvus.io/docs/multi-vector-search.md
            ranker_params={"k": k},
        )
        return results
