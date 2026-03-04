import asyncio

import frappe
from pydantic_ai import ModelRetry, RunContext

from gms.ai.agents.state import AgentContext
from gms.ai.kb.kb import SearchResult


def query_filter_for_grant():
    expr_part = []
    grants = [grant["name"] for grant in frappe.get_list("Grant", fields=["name"])]
    if len(grants) > 0:
        escaped = ",".join([f"'{g}'" for g in grants])
        expr_part.append(f"grant_id IN [{escaped}]")
    else:
        expr_part.append("grant_id == 'invalid'")

    if len(expr_part) > 0:
        expr = " or ".join(expr_part)
        print(f"Using Filter exppression {expr}")
        return expr
    return None


async def perform_search(ctx: RunContext[AgentContext], query: list[str], k: int):
    kb = ctx.deps.kb
    expr = query_filter_for_grant()

    tasks = [
        kb.asearch(
            q,
            limit=k,
            task_type="QUESTION_ANSWERING",
            filter_expr=expr,
            output_fields=["text", "*"],
        )
        for q in query
    ]
    query_results = await asyncio.gather(*tasks)
    unique_results: list[SearchResult] = []
    unique_ids: set[str] = set()

    for search_result in query_results:
        for result in search_result:
            if result.id in unique_ids:
                continue
            unique_ids.add(result.id)
            unique_results.append(result)

    print(f"Result Count {len(unique_results)}")
    return unique_results


def to_document_content(result: SearchResult):
    return f"""\
            <document>
                <content>{result.text}</content>
                <content>{result.metadata}</content>
            </document>
            """


async def read_knowledge_base(ctx: RunContext[AgentContext], query: list[str]):
    """
    Reads the knowledgebase to find out answer query
    :type query: list[str] : Query to search for. Ideally each query should be looking to find something different
    :returns Document talking about the query including the source
    """
    k = ctx.deps.agent_conf.knowledgebase_total_retrieval or 20

    # Notify and trigger search

    await ctx.deps.add_kb_search_step(queries=query, limit=k)

    documents = await perform_search(ctx, query, k=k)

    if len(documents) == 0:
        return ModelRetry(f"No result for {','.join(query)}. Try something else")

    # Notify reading sources
    await ctx.deps.add_browse_kb_result_step(
        sources=[
            f"{d.metadata.get('filename', 'unknown')}#{d.metadata.get('page_no', '')}"
            for d in documents
        ]
    )

    # Prepare content to be shared as tool response
    content = [to_document_content(doc) for doc in documents]
    final_content = "\n".join(content)
    return final_content
