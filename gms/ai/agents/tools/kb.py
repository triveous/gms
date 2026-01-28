import asyncio

import frappe
from langchain_core.documents.base import Document
from pydantic_ai import ModelRetry, RunContext

from gms.ai.agents.state import AgentContext


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

    tasks = [kb.retrieve_raw(q, k=k, expr=expr) for q in query]
    query_documents = await asyncio.gather(*tasks)
    unique_documents = []
    unique_ids = set()

    for search_document in query_documents:
        for d in search_document:
            document: Document = d
            id = document.metadata["pk"]
            if id not in unique_ids:
                unique_ids.add(id)
                unique_documents.append(document)

    print(f"Result Count {len(unique_documents)}")
    return unique_documents


def to_document_content(doc: Document):
    return f"""\
            <document>
                <content>{doc.page_content}</content>
                <content>{doc.metadata}</content>
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
        sources=[f"{d.metadata['filename']}#{d.metadata['page_no']}" for d in documents]
    )

    # Prepare content to be shared as tool response
    content = [to_document_content(doc) for doc in documents]
    final_content = "\n".join(content)
    return final_content
