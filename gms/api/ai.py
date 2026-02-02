import frappe
from gms.ai.agents_v2.agent_runner import AgentRunner
from werkzeug.wrappers import Response

runner = AgentRunner()


@frappe.whitelist()
def ask():
    thread_id = frappe.form_dict.get("thread_id")
    query = frappe.form_dict.get("query")
    if not query:
        frappe.response["http_status_code"] = 400
        frappe.throw("Missing Query")
        return

    ai_agent_id = frappe.get_cached_value("GMS Settings", "GMS Settings", "rag_agent")

    return Response(
        runner.run_ui_mode(ai_agent_id, thread_id, query),
        status=200,
        headers={
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Stream-Type": "limited",
        },
    )


@frappe.whitelist()
def history():
    thread_id = frappe.form_dict.get("thread_id")

    if not thread_id:
        frappe.throw("Missing thread")
        return

    return runner.get_history(thread_id)
