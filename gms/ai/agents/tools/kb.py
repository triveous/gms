from langchain_core.documents.base import Document
from pydantic_ai import RunContext, ToolReturn
from pydantic_ai.ui.vercel_ai.response_types import SourceDocumentChunk
from gms.ai.agents.state import AgentState
import frappe


async def read_knowledge_base(ctx: RunContext[AgentState], query: str):
    """
    Reads the knowledgebase to find out answer query
    :type query: str
    :returns Document talking about the query including the source
    """
    print(f"Performing search {query}")
    kb = ctx.deps.kb
    k = ctx.deps.agent_conf.knowledgebase_total_retrieval or 20

    expr_part = []
    grants = [grant["name"] for grant in frappe.get_list("Grant", fields=["name"])]
    if len(grants) > 0:
        escaped = ",".join([f"'{g}'" for g in grants])
        expr_part.append(f"grant_id IN [{escaped}]")
    else:
        expr_part.append("grant_id == 'invalid'")

    expr = None

    if len(expr_part) > 0:
        expr = " or ".join(expr_part)
        print(f"Using Filter exppression {expr}")

    documents = await kb.retrieve_raw(query, k=k, expr=expr)

    if len(documents) == 0:
        return "No result for the query"

    def document_content(doc: Document):
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

    #  "headings": " <SEP> ".join(chunk.meta.headings or []),
    #                 "page_no": page_no,
    #                 "mime_type": self.file_mime_type,
    #                 "filename": self.file_name,
    #                 "images": json.dumps(images),
    for d in documents:
        await ctx.deps.events.send_event(
            SourceDocumentChunk(
                source_id=d.metadata.get("filename", "unknown"),
                media_type="application/pdf",
                title=d.metadata.get("filename", "untitled"),
                filename=d.metadata.get("filename", "Missing"),
            )
        )

    final_content = None
    if has_none_text:
        final_content = ToolReturn(return_value="Knowledge updated", content=content)
    else:
        final_content = "\n".join(content)

    print(f"Researched {len(documents)} docs")
    return final_content
