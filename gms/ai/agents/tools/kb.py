from langchain_core.documents.base import Document
from pydantic_ai import RunContext, ToolReturn

from gms.ai.agents.state import AgentState


def read_knowledge_base(ctx: RunContext[AgentState], query: str):
    """
    Reads the knowledgebase to find out answer query
    :type query: str
    :returns Document talking about the query including the source
    """
    print(f"Performing search {query}")
    kb = ctx.deps.kb
    k = ctx.deps.agent_conf.knowledgebase_total_retrieval or 20

    expr_part = []
    expr = None

    if len(expr_part) > 0:
        expr = " or ".join(expr_part)

    documents = kb.retrieve_raw(query, k=k, expr=expr)

    if len(documents) == 0:
        return "No result for the query"

    def document_content(doc: Document):
        raw_text = doc.metadata.get("raw_text")
        summary = doc.metadata.get("summary")
        if raw_text and summary:
            doc.metadata.pop("raw_text")
            doc.metadata.pop("summary")
            return f"""\
            <document>
                <content>{raw_text}</content>
                <content>{doc.metadata}</content>
            </document>
            """

        return f"""\
            <document>
                <content>{doc.page_content}</content>
                <content>{doc.metadata}</content>
            </document>
            """

    content = []
    has_none_text = False
    for doc in documents:
        content.append(document_content(doc))
        # if doc.metadata.get("images") is None:
        #     continue
        # images = json.loads(doc.metadata["images"])
        # for img in images:
        #     try:
        #         if img["uri"] is not None:
        #             mime_type = img["mime_type"]
        #             uri = img["uri"]
        #             image = PILImage.open(img["uri"])
        #             buffer = BytesIO()
        #             image.save(buffer, format=mime_type.split("/")[1])
        #             content.append(
        #                 BinaryImage(
        #                     data=buffer.getvalue(),
        #                     media_type=mime_type,
        #                     identifier=uri,
        #                 )
        #             )
        #     except Exception:
        #         pass

    for d in documents:
        ctx.deps.sources.append(d)

    final_content = None
    if has_none_text:
        final_content = ToolReturn(return_value="Knowledge updated", content=content)
    else:
        final_content = "\n".join(content)

    print(f"Researched {len(documents)} docs")
    return final_content
