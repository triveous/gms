import frappe
from gms.ai.agents.base.knowledge_base import KnowledgeBase
from gms.ai.agents.chat_agent import SupportDependencies, chat_agent
from gms.ai.doctype.ai_conversation.ai_conversation import AIConversation
from gms.utils.iterator import stream_async_iterator
from pydantic import ValidationError
from pydantic_ai import AgentRun, ModelMessagesTypeAdapter
from pydantic_ai.ui import SSE_CONTENT_TYPE
from pydantic_ai.ui.vercel_ai import VercelAIAdapter
from pydantic_core import to_jsonable_python
from werkzeug.wrappers import Response


@frappe.whitelist()
def run():
    if not frappe.request.data:
        frappe.throw("Missing details to initiate a chat")
        return

    try:
        run_input = VercelAIAdapter.build_run_input(frappe.request.data)
    except ValidationError:
        frappe.response["http_status_code"] = 422
        frappe.throw("Invalid Request Data")
        return

    # Load the message history
    conversation = frappe.get_doc("AI Conversation", run_input.id)
    message_history = None
    if conversation.messages is not None:
        message_history = ModelMessagesTypeAdapter.validate_json(conversation.messages)
        print("Message history loaded")
    else:
        print("No message history")

    # Create a convertor which convert the model response to UIMessage responnse
    accept = frappe.request.headers.get("accept", SSE_CONTENT_TYPE)
    adapter = VercelAIAdapter(agent=chat_agent, run_input=run_input, accept=accept)
    deps = SupportDependencies(kb=KnowledgeBase())
    event_stream = adapter.run_stream(
        deps=deps,
        message_history=message_history,
        on_complete=lambda run: save_agent_run(converstion=conversation, run=run),
    )

    # Serialized the [UIMessage] to string which text stream
    sse_event_stream = adapter.encode_stream(event_stream)

    return Response(
        stream_async_iterator(sse_event_stream),
        status=200,
        headers={
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Stream-Type": "limited",
        },
    )


def save_agent_run(converstion: AIConversation, run: AgentRun):
    messages_json = to_jsonable_python(run.all_messages_json())
    converstion.set_history(messages_json)
    converstion.save()
    frappe.db.commit()


@frappe.whitelist()
def history():
    conversation_id = frappe.form_dict.get("conversation_id")
    conversation: AIConversation = frappe.get_doc("AI Conversation", conversation_id)
    if conversation.messages is not None:
        message_history = ModelMessagesTypeAdapter.validate_json(conversation.messages)
        history = VercelAIAdapter.dump_messages(message_history)
        return to_jsonable_python(history)

    return []
