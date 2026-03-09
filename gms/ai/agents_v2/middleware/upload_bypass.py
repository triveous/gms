import traceback
from typing import Any

import frappe
from langchain.agents.middleware import AgentMiddleware
from langchain.agents.middleware.types import ModelRequest, ModelResponse
from langchain_core.messages import AIMessage, HumanMessage

from gms.ai.agents_v2.utils.ui_stream_writer import get_ui_stream_writer


class UploadKeywordBypassMiddleware(AgentMiddleware):
    """Middleware that intercepts 'upload' keyword and bypassed the LLM entirely."""

    def wrap_model_call(
        self,
        request: ModelRequest[Any],
        handler: Any,
    ) -> Any:
        # Check if we should bypass
        if self._should_bypass(request):
            return self._handle_bypass()
        
        # Otherwise, proceed as normal
        return handler(request)

    async def awrap_model_call(
        self,
        request: ModelRequest[Any],
        handler: Any,
    ) -> Any:
        if self._should_bypass(request):
            return self._handle_bypass()
        return await handler(request)

    def _should_bypass(self, request: ModelRequest[Any]) -> bool:
        messages = request.state.get("messages", [])
        if not messages:
            return False

        last_message = messages[-1]
        if not isinstance(last_message, HumanMessage):
            return False

        query = last_message.content
        if isinstance(query, list):
            # Try to extract string if it's a list
            texts = [
                c["text"]
                for c in query
                if isinstance(c, dict) and c.get("type") == "text"
            ]
            query = " ".join(texts)

        if not isinstance(query, str) or "upload" not in query.lower():
            return False
            
        return True

    def _handle_bypass(self) -> Any:
        writer = get_ui_stream_writer()
        try:
            from gms.permission import get_organization_user

            org_user = get_organization_user(frappe.session.user)
            if not org_user:
                msg = "You are not associated with any organization. Only members of a Grantee organization are allowed to upload files."
                writer.write({"type": "text", "text": msg})
                return AIMessage(content=msg)

            is_grantee = frappe.db.exists(
                "Grant Contributor",
                {
                    "organization": org_user.get("organization"),
                    "contribution_type": "Grantee",
                },
            )
            if not is_grantee:
                msg = "You are not allowed to access this feature. Only members of a Grantee organization can upload files."
                writer.write({"type": "text", "text": msg})
                return AIMessage(content=msg)

            doc = frappe.new_doc("Grant Document Extraction Task")
            doc.status = "Submitting"
            doc.reviewed_by = frappe.session.user
            doc.insert(ignore_permissions=True)
            frappe.db.commit()

            task_id = doc.name

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

            # Stream task event to UI
            writer.write_task({"id": task_id, "status": "Submitting", "grant_id": grant_id})

            # Return an empty AIMessage without tool calls so the agent completes
            return AIMessage(content="")

        except Exception as e:
            traceback.print_exception(e)
            writer.write({"type": "error", "error": str(e)})
            return AIMessage(content=f"Error: {e}")

