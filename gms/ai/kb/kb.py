"""Knowledge Base module using pymilvus for hybrid search with RRF ranking.

This module provides a Knowledge class that handles:
- Document indexing with dense (embedding) and sparse (BM25) vectors
- Hybrid search using RRF (Reciprocal Rank Fusion) ranking
"""

from dataclasses import dataclass
from typing import Any, Literal, NotRequired, TypedDict

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from pymilvus import (
    AnnSearchRequest,
    DataType,
    Function,
    FunctionType,
    MilvusClient,
    RRFRanker,
)


@dataclass
class SearchResult:
    """Represents a single search result from the knowledge base."""

    id: str
    text: str
    metadata: dict[str, Any]
    score: float


class Document(TypedDict):
    """Document structure for indexing."""

    text: str
    id: NotRequired[str | int]


class Knowledge:
    """Knowledge base class for hybrid search using pymilvus.

    Uses dense vectors (from embeddings) and sparse vectors (BM25) with
    RRF ranking for optimal retrieval results.
    """

    def __init__(
        self,
        uri: str,
        token: str,
        collection_name: str = "documents",
        embedding_model: str = "gemini-embedding-001",
        embedding_dimensions: int = 3072,
    ):
        """Initialize the Knowledge base.

        Args:
            uri: Milvus connection URI
            token: Authentication token
            collection_name: Name of the collection to use
            embedding_model: Name of the embedding model
            embedding_dimensions: Dimensionality of dense embeddings
        """
        self.uri = uri
        self.token = token
        self.collection_name = collection_name
        self.embedding_dimensions = embedding_dimensions

        # Single embedding function - task_type is passed at call time
        self._embedding_fn = GoogleGenerativeAIEmbeddings(
            model=embedding_model,
            output_dimensionality=embedding_dimensions,
        )

        # Connect to Milvus
        self.client = MilvusClient(uri=uri, token=token)

        # Ensure collection exists
        self._ensure_collection()

    def _ensure_collection(self):
        """Create collection if it doesn't exist."""
        if self.client.has_collection(self.collection_name):
            return

        # Define schema
        schema = self.client.create_schema(auto_id=True, enable_dynamic_field=True)

        # Primary key
        schema.add_field(
            field_name="id",
            datatype=DataType.INT64,
            is_primary=True,
            auto_id=True,
        )

        # Text field for content
        schema.add_field(
            field_name="text",
            datatype=DataType.VARCHAR,
            max_length=65535,
            enable_analyzer=True,
            enable_match=True,
            analyzer_params={"type": "english"},
        )

        # Dense vector field for embeddings
        schema.add_field(
            field_name="dense",
            datatype=DataType.FLOAT_VECTOR,
            dim=self.embedding_dimensions,
        )

        # Sparse vector field for BM25
        schema.add_field(
            field_name="sparse",
            datatype=DataType.SPARSE_FLOAT_VECTOR,
        )

        # Add BM25 function to generate sparse vectors from text
        bm25_function = Function(
            name="bm25_fn",
            function_type=FunctionType.BM25,
            input_field_names=["text"],
            output_field_names=["sparse"],
        )
        schema.add_function(bm25_function)

        # Define index params
        index_params = self.client.prepare_index_params()

        # Dense vector index (HNSW with cosine similarity)
        index_params.add_index(
            field_name="dense",
            index_name="text_dense_index",
            index_type="HNSW",
            metric_type="COSINE",
            params={"M": 16, "efConstruction": 256},
        )

        # Sparse vector index (for BM25)
        index_params.add_index(
            field_name="sparse",
            index_type="SPARSE_INVERTED_INDEX",
            metric_type="BM25",
        )

        # Create collection
        self.client.create_collection(
            collection_name=self.collection_name,
            schema=schema,
            index_params=index_params,
        )

    def index_documents(
        self,
        documents: list[Document],
    ) -> list[int]:
        """Index documents into the knowledge base.

        Args:
            documents: List of documents with required 'text' field and optional 'id' field.
                       Additional fields will be stored as dynamic fields.

        Returns:
            List of inserted document IDs.
        """
        if not documents:
            return []

        # Extract text for embedding
        texts = [doc["text"] for doc in documents]

        # Generate dense embeddings using RETRIEVAL_DOCUMENT task type
        embeddings = self._embedding_fn.embed_documents(
            texts, task_type="RETRIEVAL_DOCUMENT"
        )

        # Prepare data for insertion
        data = []
        for i, doc in enumerate(documents):
            record = {
                "text": doc["text"],
                "dense": embeddings[i],
            }
            # Add any additional metadata fields (except 'text' which is already added)
            for key, value in doc.items():
                if key != "text":
                    record[key] = value
            data.append(record)

        # Insert into collection
        result = self.client.insert(
            collection_name=self.collection_name,
            data=data,
        )

        return result.get("ids", [])

    def search(
        self,
        query: str,
        limit: int = 10,
        rrf_k: int = 60,
        output_fields: list[str] | None = None,
        task_type: Literal[
            "RETRIEVAL_QUERY", "QUESTION_ANSWERING", "FACT_VERIFICATION"
        ] = "RETRIEVAL_QUERY",
        filter_expr: str | None = None,
    ) -> list[SearchResult]:
        """Perform hybrid search using dense and sparse vectors with RRF ranking.

        Args:
            query: Search query string
            limit: Maximum number of results to return
            rrf_k: RRF ranking parameter (higher = more weight to lower ranks)
            output_fields: Fields to include in results (default: text + all dynamic)
            task_type: Embedding task type for query. Options:
                - RETRIEVAL_QUERY: Standard retrieval (default)
                - QUESTION_ANSWERING: For QA use cases
                - FACT_VERIFICATION: For fact-checking use cases
            filter_expr: Optional Milvus filter expression (e.g., "grant_id IN ['G1','G2']")

        Returns:
            List of SearchResult objects
        """
        if output_fields is None:
            output_fields = ["text", "*"]

        # Generate query embedding with the specified task type
        query_embedding = self._embedding_fn.embed_query(query, task_type=task_type)

        # Dense search request
        dense_req = AnnSearchRequest(
            data=[query_embedding],
            anns_field="dense",
            param={"metric_type": "COSINE", "params": {"ef": 100}},
            limit=limit,
            expr=filter_expr,
        )

        # Sparse search request (BM25)
        # For BM25, we pass the query text and Milvus handles tokenization
        sparse_req = AnnSearchRequest(
            data=[query],
            anns_field="sparse",
            param={"metric_type": "BM25"},
            limit=limit,
            expr=filter_expr,
        )

        # Perform hybrid search with RRF ranking
        try:
            results = self.client.hybrid_search(
                collection_name=self.collection_name,
                reqs=[dense_req, sparse_req],
                ranker=RRFRanker(k=rrf_k),
                limit=limit,
                output_fields=output_fields,
            )
        except Exception as e:
            import traceback

            traceback.print_exception(e)

        # Convert to SearchResult objects
        search_results = []
        for hits in results:
            for hit in hits:
                entity = hit.get("entity", {})
                metadata = {k: v for k, v in entity.items() if k != "text"}
                search_results.append(
                    SearchResult(
                        id=str(hit.get("id", "")),
                        text=entity.get("text", ""),
                        metadata=metadata,
                        score=hit.get("distance", 0.0),
                    )
                )

        return search_results

    async def asearch(
        self,
        query: str,
        limit: int = 20,
        rrf_k: int = 60,
        output_fields: list[str] | None = None,
        task_type: Literal[
            "RETRIEVAL_QUERY", "QUESTION_ANSWERING", "FACT_VERIFICATION"
        ] = "RETRIEVAL_QUERY",
        filter_expr: str | None = None,
    ) -> list[SearchResult]:
        """Async version of search. Currently wraps sync version.

        TODO: Use async client when pymilvus supports it.
        """
        # pymilvus doesn't have native async support yet
        # This is a placeholder for future async implementation
        return self.search(query, limit, rrf_k, output_fields, task_type, filter_expr)

    def delete_documents(self, ids: list[int]) -> int:
        """Delete documents by their IDs.

        Args:
            ids: List of document IDs to delete

        Returns:
            Number of documents deleted
        """
        if not ids:
            return 0

        self.client.delete(
            collection_name=self.collection_name,
            ids=ids,
        )
        return len(ids)

    def delete_documents_by_expression(self, expression: str) -> None:
        """Delete documents matching a filter expression.

        Args:
            expression: Milvus filter expression (e.g., "file_name == 'doc.pdf'")
        """
        self.client.delete(
            collection_name=self.collection_name,
            filter=expression,
        )

    def drop_collection(self):
        """Drop the entire collection. Use with caution!"""
        if self.client.has_collection(self.collection_name):
            self.client.drop_collection(self.collection_name)
