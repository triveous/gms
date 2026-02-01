from langchain.agents.middleware import AgentMiddleware
from langchain.tools import ToolRuntime
from langchain_core.messages import ToolMessage
from langchain_core.tools import StructuredTool
from langgraph.graph.state import Command
from uuid import uuid4

from gms.ai.agents_v2.middleware.steps import SearchKBStep
from gms.ai.agents_v2.utils import get_ui_stream_writer
from gms.ai.kb.kb import Knowledge

READ_KNOWLEDGE_BASE_TOOL_DESCRIPTION = """Reads and retrieves relevant content from the knowledge base based on the given query.
Search for relevant documents in the knowledge base based on the given query.
"""


def create_search_step(query: list[str]) -> SearchKBStep:
    """Create a new search step with in-progress status."""
    return SearchKBStep(
        id=str(uuid4()),
        type="search_kb",
        content={"query": query},
        progress="in-progress",
    )


def complete_search_step(
    step: SearchKBStep, query: list[str], results_count: int
) -> SearchKBStep:
    """Mark a search step as complete with results count."""
    step["content"] = {"query": query, "results_count": results_count}
    step["progress"] = "done"
    return step


def create_read_knowledgebase_tool(knowledge: Knowledge, limit: int = 10):
    """Create a knowledge base search tool using the Knowledge class.

    Args:
        knowledge: Knowledge instance for searching
        limit: Maximum number of results per query
    """

    async def aread_knowledge_base(query: list[str], runtime: ToolRuntime):
        """Async version of knowledge base search."""
        writer = get_ui_stream_writer()

        # Add the search step
        step = create_search_step(query)
        writer.write_step(step)

        all_results = []
        for q in query:
            results = await knowledge.asearch(
                q,
                limit=limit,
                task_type="QUESTION_ANSWERING",
            )
            all_results.extend(results)

        if not all_results:
            return "No content found for this query. Try a different query."

        content = "\n".join([f"<content>{r.text}</content>" for r in all_results])
        print(f"Total documents found: {len(all_results)}")

        # Mark the search step as complete
        complete_search_step(step, query, len(all_results))
        writer.write_step(step)

        return Command(
            update={
                "messages": [
                    ToolMessage(content=content, tool_call_id=runtime.tool_call_id)
                ],
                "steps": [step],
            }
        )

    def read_knowledge_base(query: list[str], runtime: ToolRuntime):
        writer = get_ui_stream_writer()

        # Add the search step
        step = create_search_step(query)
        writer.write_step(step)

        all_results = []
        for q in query:
            results = knowledge.search(
                q,
                limit=limit,
                task_type="QUESTION_ANSWERING",
            )
            all_results.extend(results)

        if not all_results:
            return "No content found for this query. Try a different query."

        content = "\n".join([f"<content>{r.text}</content>" for r in all_results])
        print(f"Total documents found: {len(all_results)}")

        # Mark the search step as complete
        complete_search_step(step, query, len(all_results))
        writer.write_step(step)

        return Command(
            update={
                "messages": [
                    ToolMessage(content=content, tool_call_id=runtime.tool_call_id)
                ],
                "steps": [step],
            }
        )

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
