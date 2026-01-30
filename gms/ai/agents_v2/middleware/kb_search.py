import asyncio

from langchain.agents.middleware import AgentMiddleware
from langchain_core.tools import StructuredTool
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_milvus import Milvus, BM25BuiltInFunction

READ_KNOWLEDGE_BASE_TOOL_DESCRIPTION = """Reads and retrieves relevant content from the knowledge base based on the given query
Search for relevant documents in the knowledge base based on the given query.
"""


def create_read_knowledgebase_tool(retriever: VectorStoreRetriever):
    async def aread_knowledge_base(query: list[str]):
        try:
            nested_doc = await asyncio.gather(*[retriever.ainvoke(q) for q in query])
            documents = [doc for d in nested_doc for doc in d]
            doc_sources = [
                str(d.metadata.get("file_name", "Default")) for d in documents
            ]
            content = "\n".join(
                [f"<content>{doc.page_content}</content>" for doc in documents]
            )
            if len(documents) == 0:
                return "Not content found for this. Try different query"

            print(f"Total document found: {len(documents)}")
            return content
        except Exception as e:
            return str(e)

    def read_knowledge_base(query: list[str]):
        """
        Reads and retrieves relevant content from the knowledge base based on the given query.

        Search for relevant documents in the knowledge base based on the given query.

        :param query: The user query to search the knowledge base.
        :type query: str
        :return: The retrieved chunk of content from document
        """

        try:
            nested_doc = [retriever.invoke(q) for q in query]
            documents = [doc for d in nested_doc for doc in d]
            doc_sources = [
                str(d.metadata.get("file_name", "Default")) for d in documents
            ]
            content = "\n".join(
                [f"<content>{doc.page_content}</content>" for doc in documents]
            )
            if len(documents) == 0:
                return "Not content found for this. Try different query"

            print(f"Total document found: {len(documents)}")
            return content
        except Exception as e:
            return str(e)

    return StructuredTool.from_function(
        func=read_knowledge_base,
        coroutine=aread_knowledge_base,
        name="read_knowledge_base",
        description=READ_KNOWLEDGE_BASE_TOOL_DESCRIPTION,
    )


class KBSearchMiddleware(AgentMiddleware):
    def __init__(
        self,
        connection_uri: str,
        token: str,
        collection: str = "documents",
        rrf_ranker_k=20,
    ):
        retriever = self.get_retriever(connection_uri, token, collection, rrf_ranker_k)
        self.read_knowledge_base = create_read_knowledgebase_tool(retriever)
        self.tools = [self.read_knowledge_base]

    @staticmethod
    def get_retriever(
        connection_uri: str, token: str, collection: str, rrf_ranker_k: int
    ):
        embedding_function = GoogleGenerativeAIEmbeddings(
            model="gemini-embedding-001",
            task_type="RETRIEVAL_QUERY",
            output_dimensionality=3072,
        )

        dense_index_param = {"metric_type": "COSINE", "index_type": "HNSW"}
        sparse_index_param = {"metric_type": "BM25", "index_type": "AUTOINDEX"}

        milvus = Milvus(
            auto_id=True,
            embedding_function=embedding_function,
            collection_name=collection,
            builtin_function=BM25BuiltInFunction(),
            vector_field=["dense", "sparse"],
            enable_dynamic_field=True,
            connection_args={
                "uri": connection_uri,
                "token": token,
            },
            index_params=[dense_index_param, sparse_index_param],
            drop_old=False,
        )

        return milvus.as_retriever(
            search_type="similarity",
            ranker_type="rrf",
            ranker_params={"k": rrf_ranker_k},
        )
