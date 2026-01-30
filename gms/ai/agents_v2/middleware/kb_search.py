from langchain.agents.middleware import AgentMiddleware
from langchain_core.tools import StructuredTool

from gms.ai.kb.kb import Knowledge

READ_KNOWLEDGE_BASE_TOOL_DESCRIPTION = """Reads and retrieves relevant content from the knowledge base based on the given query.
Search for relevant documents in the knowledge base based on the given query.
"""


def create_read_knowledgebase_tool(knowledge: Knowledge, limit: int = 10):
    """Create a knowledge base search tool using the Knowledge class.

    Args:
        knowledge: Knowledge instance for searching
        limit: Maximum number of results per query
    """

    async def aread_knowledge_base(query: list[str]):
        """Async version of knowledge base search."""
        try:
            all_results = []
            for q in query:
                results = await knowledge.asearch(q, limit=limit)
                all_results.extend(results)

            if not all_results:
                return "No content found for this query. Try a different query."

            content = "\n".join([f"<content>{r.text}</content>" for r in all_results])
            print(f"Total documents found: {len(all_results)}")
            return content
        except Exception as e:
            return str(e)

    def read_knowledge_base(query: list[str]):
        """Sync version of knowledge base search."""
        try:
            all_results = []
            for q in query:
                results = knowledge.search(q, limit=limit)
                all_results.extend(results)

            if not all_results:
                return "No content found for this query. Try a different query."

            content = "\n".join([f"<content>{r.text}</content>" for r in all_results])
            print(f"Total documents found: {len(all_results)}")
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
    """Middleware that provides knowledge base search capabilities to agents.

    Uses the Knowledge class for hybrid search with RRF ranking.
    """

    def __init__(
        self,
        knowledge: Knowledge,
        search_limit: int = 20,
    ):
        """Initialize the middleware with a Knowledge instance.

        Args:
            knowledge: Knowledge instance (cached externally)
            search_limit: Maximum results per query
        """
        self.knowledge = knowledge
        self.read_knowledge_base = create_read_knowledgebase_tool(
            knowledge, limit=search_limit
        )
        self.tools = [self.read_knowledge_base]
