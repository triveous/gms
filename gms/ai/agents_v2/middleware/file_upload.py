from typing import Any

from langchain.agents.middleware import AgentMiddleware
from langchain.tools import ToolRuntime
from langchain_core.messages import ToolMessage
from langchain_core.tools import StructuredTool
from langgraph.types import Command

from gms.ai.agents_v2.utils.ui_stream_writer import get_ui_stream_writer


def _permission_denied_response(runtime: ToolRuntime, message: str) -> Command:
    """Stream a text event with a permission-denied message and return a ToolMessage."""
    writer = get_ui_stream_writer()
    writer.write({"type": "text", "text": message})
    return Command(
        update={
            "messages": [
                ToolMessage(
                    content=message,
                    tool_call_id=runtime.tool_call_id,
                )
            ],
        }
    )


def _request_file_upload(runtime: ToolRuntime):
    """Request the user to upload a document/file for extraction. Call this tool when the user expresses intent to upload a file."""
    import frappe
    from gms.permission import get_organization_user

    # Permission check: user must belong to an organization that is a Grantee on at least one Grant
    org_user = get_organization_user(frappe.session.user)
    if not org_user:
        return _permission_denied_response(
            runtime,
            "You are not associated with any organization. Only members of a Grantee organization are allowed to upload files.",
        )

    is_grantee = frappe.db.exists(
        "Grant Contributor",
        {
            "organization": org_user.get("organization"),
            "contribution_type": "Grantee",
        },
    )
    if not is_grantee:
        return _permission_denied_response(
            runtime,
            "You are not allowed to access this feature. Only members of a Grantee organization can upload files.",
        )

    doc = frappe.new_doc("Grant Document Extraction Task")
    doc.status = "Submitting"
    doc.reviewed_by = frappe.session.user
    doc.insert(ignore_permissions=True)
    frappe.db.commit()

    task_id = doc.name

    # Fetch the grant where the user's organization is a Grantee contributor
    grantee_contributor = frappe.db.get_value(
        "Grant Contributor",
        {
            "organization": org_user.get("organization"),
            "contribution_type": "Grantee",
        },
        ["parent"],
        as_dict=True,
    )
    grant_id = grantee_contributor.get("parent") if grantee_contributor else None

    writer = get_ui_stream_writer()
    writer.write_task({"id": task_id, "status": "Submitting", "grant_id": grant_id})

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
