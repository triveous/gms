from typing import Any

from langchain.agents.middleware import AgentMiddleware
from langchain.tools import ToolRuntime
from langchain_core.messages import ToolMessage
from langchain_core.tools import StructuredTool
from langgraph.types import Command

from gms.ai.agents_v2.utils.ui_stream_writer import get_ui_stream_writer


def _request_file_upload(runtime: ToolRuntime):
    """Request the user to upload a document/file for extraction. Call this tool when the user expresses intent to upload a file."""
    import frappe

    doc = frappe.new_doc("Grant Document Extraction Task")
    doc.status = "Submitting"
    doc.reviewed_by = frappe.session.user
    doc.insert(ignore_permissions=True)
    frappe.db.commit()

    task_id = doc.name

    data_payload = {"task": task_id, "status": "Submitting"}

    writer = get_ui_stream_writer()
    writer.write_task({"id": task_id, "status": "Submitting", "data": data_payload})

    return Command(
        update={
            "messages": [
                ToolMessage(
                    content=f"Created Grant Document Extraction Task '{task_id}'. Awaiting user file upload. Tell the user you have opened the file upload prompt.",
                    tool_call_id=runtime.tool_call_id,
                    additional_kwargs={"task_id": task_id},
                )
            ],
        }
    )


request_file_upload_tool = StructuredTool.from_function(
    func=_request_file_upload,
    name="request_file_upload",
    description="Request the user to upload a document/file for extraction. Call this tool when the user expresses intent to upload a file.",
)


class FileUploadMiddleware(AgentMiddleware):
    """Middleware that provides file upload capabilities to agents."""

    def __init__(self):
        """Initialize the middleware."""
        self.tools = [request_file_upload_tool]
