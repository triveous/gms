from langchain.agents.middleware import AgentMiddleware
from langchain.tools import ToolRuntime
from langchain_core.messages import ToolMessage
from langchain_core.tools import StructuredTool
from langgraph.graph.state import Command
from uuid import uuid4

from gms.ai.agents_v2.middleware.steps import (
    SearchKBStep,
    BrowseKBStep,
    BrowseKBSource,
)
from gms.ai.agents_v2.utils import get_ui_stream_writer
from gms.ai.kb.kb import Knowledge

READ_KNOWLEDGE_BASE_TOOL_DESCRIPTION = """Reads and retrieves relevant content from the knowledge base based on the given query.
Search for relevant documents in the knowledge base based on the given query.
"""


def _get_active_goal_id(runtime: ToolRuntime) -> str | None:
    """Get the active goal ID from the last goal in state.

    Args:
        runtime: ToolRuntime with access to agent state

    Returns:
        ID of the last (active) goal, or None if no goals
    """
    goals = runtime.state.get("goals", [])
    if goals:
        return goals[-1].get("id")
    return None


def create_search_step(query: list[str], goal_id: str | None = None) -> SearchKBStep:
    """Create a new search step with in-progress status.

    Args:
        query: Search queries
        goal_id: ID of the goal this step is linked to
    """
    return SearchKBStep(
        id=str(uuid4()),
        type="search_kb",
        goal_id=goal_id,
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


def create_browse_step(results: list, goal_id: str | None = None) -> BrowseKBStep:
    """Create a browse step showing unique source documents.

    Extracts unique sources from search results based on ai_document_id.

    Args:
        results: List of SearchResult objects with metadata containing
                ai_document_id and filename fields.
        goal_id: ID of the goal this step is linked to

    Returns:
        BrowseKBStep with unique sources.
    """
    # Extract unique sources using ai_document_id
    seen_ids: set[str] = set()
    sources: list[BrowseKBSource] = []

    for result in results:
        metadata = result.metadata
        doc_id = metadata.get("ai_document_id", "")
        filename = metadata.get("filename", "")

        # Skip if we've already seen this document
        if doc_id and doc_id in seen_ids:
            continue
        if not doc_id and filename in seen_ids:
            continue

        # Add to seen set
        if doc_id:
            seen_ids.add(doc_id)
        elif filename:
            seen_ids.add(filename)

        # Add source
        sources.append(
            BrowseKBSource(
                id=doc_id or filename,
                title=filename,
            )
        )

    return BrowseKBStep(
        id=str(uuid4()),
        type="browse_kb",
        goal_id=goal_id,
        content={"sources": sources},
        progress="done",
    )


def create_read_knowledgebase_tool(knowledge: Knowledge, limit: int = 10):
    """Create a knowledge base search tool using the Knowledge class.

    Args:
        knowledge: Knowledge instance for searching
        limit: Maximum number of results per query
    """

    async def aread_knowledge_base(query: list[str], runtime: ToolRuntime):
        """Async version of knowledge base search."""
        writer = get_ui_stream_writer()

        # Get current goal ID for step linking (last goal is active)
        goal_id = _get_active_goal_id(runtime)

        # Add the search step
        step = create_search_step(query, goal_id=goal_id)
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

        # Create browse step showing sources
        browse_step = create_browse_step(all_results, goal_id=goal_id)
        writer.write_step(browse_step)

        return Command(
            update={
                "messages": [
                    ToolMessage(content=content, tool_call_id=runtime.tool_call_id)
                ],
                "steps": [step, browse_step],
            }
        )

    def read_knowledge_base(query: list[str], runtime: ToolRuntime):
        writer = get_ui_stream_writer()

        # Get current goal ID for step linking (last goal is active)
        goal_id = _get_active_goal_id(runtime)

        # Add the search step
        step = create_search_step(query, goal_id=goal_id)
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

        # Create browse step showing sources
        browse_step = create_browse_step(all_results, goal_id=goal_id)
        writer.write_step(browse_step)

        return Command(
            update={
                "messages": [
                    ToolMessage(content=content, tool_call_id=runtime.tool_call_id)
                ],
                "steps": [step, browse_step],
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
