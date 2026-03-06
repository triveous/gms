from langchain.agents.middleware import AgentMiddleware
from langchain.tools import ToolRuntime
from langchain_core.messages import ToolMessage
from langchain_core.tools import StructuredTool
from langgraph.graph.state import Command
from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor, as_completed
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
        page_no = metadata.get("page_no", None)
        title = filename

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
        sources.append(BrowseKBSource(id=doc_id or filename, title=title, page=page_no))

    return BrowseKBStep(
        id=str(uuid4()),
        type="browse_kb",
        goal_id=goal_id,
        content={"sources": sources},
        progress="done",
    )


OUTPUT_FIELDS = ["text", "ai_document_id", "filename", "page_no"]





def create_read_knowledgebase_tool(
    knowledge: Knowledge, limit: int = 10, max_result: int = 50
):
    """Create a knowledge base search tool using the Knowledge class.

    Args:
        knowledge: Knowledge instance for searching
        limit: Maximum number of results per query
        max_result: Maximum number of total unique results to return
    """
    print(f"Setting up search limit {limit} max_result {max_result}")

    def _build_grant_filter(runtime: ToolRuntime) -> str | None:
        """Build Milvus filter expression from data_overview state.

        Uses grant names from data_overview loaded by DataOverviewMiddleware.
        """
        import frappe

        grants = frappe.get_list("Grant")

        if not grants or len(grants) == 0:
            # No accessible grants - return expression that matches nothing
            return "grant_id == 'invalid'"

        # Build filter expression: grant_id IN ['grant1', 'grant2', ...]
        grant_names = [g["name"] for g in grants if g.get("name")]
        if grant_names:
            escaped = ",".join([f"'{g}'" for g in grant_names])
            return f"grant_id IN [{escaped}]"

        return None

    async def aread_knowledge_base(query: list[str], runtime: ToolRuntime):
        """Async version of knowledge base search."""
        writer = get_ui_stream_writer()

        # Get current goal ID for step linking (last goal is active)
        goal_id = _get_active_goal_id(runtime)

        # Add the search step
        step = create_search_step(query, goal_id=goal_id)
        writer.write_step(step)

        # Build grant filter from data_overview state
        filter_expr = _build_grant_filter(runtime)

        all_results = []
        for q in query:
            results = await knowledge.asearch(
                q,
                limit=limit,
                task_type="QUESTION_ANSWERING",
                filter_expr=filter_expr,
                output_fields=OUTPUT_FIELDS,
            )
            all_results.extend(results)

        # Mark the search step as complete
        complete_search_step(step, query, len(all_results))
        writer.write_step(step)

        if not all_results:
            return "No content found for this query. Try a different query."

        # Sort results by score (descending)
        all_results.sort(key=lambda r: r.score, reverse=True)

        # Deduplicate results by ID and limit to max 50
        seen_ids: set[str] = set()
        unique_results = []
        for r in all_results:
            if r.id not in seen_ids:
                seen_ids.add(r.id)
                unique_results.append(r)
                if len(unique_results) >= max_result:
                    break

        content = "\n".join(
            [
                f"""<document>
                    <content>{r.text}</content>
                </document>"""
                for r in unique_results
            ]
        )


        print(f"Unique: {unique_results} Total: {all_results}")
        print(
            f"Total documents returned: {len(unique_results)} (from {len(all_results)} results)"
        )

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

        # Build grant filter from data_overview state
        filter_expr = _build_grant_filter(runtime)
        print(filter_expr)

        all_results = []
        with ThreadPoolExecutor(max_workers=min(len(query), 5)) as executor:
            futures = {
                executor.submit(
                    knowledge.search,
                    q,
                    limit=limit,
                    task_type="QUESTION_ANSWERING",
                    filter_expr=filter_expr,
                    output_fields=OUTPUT_FIELDS,
                ): q
                for q in query
            }
            for future in as_completed(futures):
                try:
                    results = future.result()
                    all_results.extend(results)
                except Exception as e:
                    print(f"Search failed for query {futures[future]}: {e}")

        # Mark the search step as complete
        complete_search_step(step, query, len(all_results))
        writer.write_step(step)

        if not all_results:
            return "No content found for this query. Try a different query."

        # Sort results by score (descending)
        all_results.sort(key=lambda r: r.score, reverse=True)

        # Deduplicate results by ID and limit to max 50
        seen_ids: set[str] = set()
        unique_results = []
        for r in all_results:
            if r.id not in seen_ids:
                seen_ids.add(r.id)
                unique_results.append(r)
                if len(unique_results) >= max_result:
                    break

        content = "\n".join(
            [
                f"""<document>
                    <content>{r.text}</content>
                </document>"""
                for r in unique_results
            ]
        )


        print(f"Unique: {unique_results} Total: {all_results}")
        print(
            f"Total documents returned: {len(unique_results)} (from {len(all_results)} results)"
        )

        # Create browse step showing sources
        browse_step = create_browse_step(unique_results, goal_id=goal_id)
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
        search_limit: int = 10,
        search_max_result: int = 50,
    ):
        """Initialize the middleware with a Knowledge instance.

        Args:
            knowledge: Knowledge instance (cached externally)
            search_limit: Maximum results per query
            search_max_result: Maximum number of total unique results to return
        """
        self.knowledge = knowledge
        self.read_knowledge_base = create_read_knowledgebase_tool(
            knowledge, limit=search_limit, max_result=search_max_result
        )
        self.tools = [self.read_knowledge_base]
