from langchain_core.documents.base import Document
from pydantic_ai import RunContext, ModelRetry
from pydantic_ai.ui.vercel_ai.response_types import SourceDocumentChunk
from gms.ai.agents.state import AgentContext
import frappe
import asyncio


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


async def perform_search(ctx: RunContext[AgentContext], query: list[str]):
    kb = ctx.deps.kb
    k = ctx.deps.agent_conf.knowledgebase_total_retrieval or 20

    await ctx.deps.add_kb_search_step(queries=query, limit=k)

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

    await ctx.deps.add_browse_kb_result_step(
        sources=[
            f"{d.metadata['filename']}#{d.metadata['page_no']}"
            for d in unique_documents
        ]
    )

    print(f"Result Count {len(unique_documents)}")
    return unique_documents


def to_document_content(doc: Document):
    return f"""\
            <document>
                <content>{doc.page_content}</content>
                <content>{doc.metadata}</content>
            </document>
            """


async def notify_source_document(
    ctx: RunContext[AgentContext], documents: list[Document]
):
    print(f"Researched {len(documents)} docs")
    for d in documents:
        await ctx.deps.events.send_event(
            SourceDocumentChunk(
                source_id=d.metadata.get("filename", "unknown"),
                media_type="application/pdf",
                title=d.metadata.get("filename", "untitled"),
                filename=d.metadata.get("filename", "Missing"),
            )
        )


async def read_knowledge_base(ctx: RunContext[AgentContext], query: list[str]):
    """
    Reads the knowledgebase to find out answer query
    :type query: list[str] : Query to search for. Ideally each query should be looking to find something different
    :returns Document talking about the query including the source
    """
    print(f"Performing search {query}")
    documents = await perform_search(ctx, query)
    if len(documents) == 0:
        return ModelRetry(f"No result for {','.join(query)}. Try something else")

    content = [to_document_content(doc) for doc in documents]
    await notify_source_document(ctx, documents=documents)
    final_content = "\n".join(content)
    return final_content
