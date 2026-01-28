import time

import frappe
from frappe import _
from gms.ai.agents.builder import build_agent
from gms.ai.agents.state import AgentRunState, AgentState, PlanBlock, AgentContext
from gms.ai.agents.ui import (
    CustomUIEventSender,
    VercelAIAdapterCustom,
)
from gms.ai.doctype.ai_conversation.ai_conversation import AIConversation
from gms.utils.iterator import stream_async_iterator
from pydantic import ValidationError
from pydantic_ai import AgentRun, ModelMessagesTypeAdapter
from pydantic_ai.ui import SSE_CONTENT_TYPE
from pydantic_ai.ui.vercel_ai import VercelAIAdapter
from pydantic_core import to_json, to_jsonable_python
from werkzeug.wrappers import Response
from gms.ai.agent_v2.graph import q


# Build RAG agent
def build_rag_agent():
    rag_agent_name = frappe.get_single_value("GMS Settings", "rag_agent")
    agent_conf = frappe.get_doc("AI Agent", rag_agent_name)
    return agent_conf, build_agent(agent_conf)


def iterator():
    state = AgentRunState()

    def emit_data(diff: list[dict]):
        return f"data: {to_json(diff)}\n\n"

    def emit_empty():
        return "data: {}\n\n"

    def encode_event(type: str):
        return f"event: {type}\n"

    i = 0
    while i < 10:
        if i == 3:
            state.step.add_intial_query_step("What is universe")
        if i == 7:
            state.step.add_kb_search_step("0", "xasda", ["TANUH"], limit=5)

        diff = state.get_diff()

        yield encode_event("message")
        yield emit_data(diff)

        time.sleep(1)
        i = i + 1

    yield encode_event("end_of_stream")
    yield emit_empty()


@frappe.whitelist(allow_guest=True)
def run2():
    query = frappe.form_dict.get("query")
    if not query:
        frappe.throw("Missing query")
        return

    return Response(
        q(query),
        status=200,
        headers={
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Stream-Type": "limited",
        },
    )


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
    # Load the message history
    conversation_id = run_input.id
    message_history = get_message_history(conversation_id)

    # Create a convertor which convert the model response to UIMessage responnse
    accept = frappe.request.headers.get("accept", SSE_CONTENT_TYPE)

    # Ensure that we have a running loop, Agent internally create an HTTP Client which uses event loop
    # Then when we create event loop for event stream, it probably replace the event loop.
    # Now wer are creating the http.AsycnClient in the agent builder, so we need to ensure that there is a running loop before that
    VercelAIAdapterCustom.set_loop()

    agent_conf, agent = build_rag_agent()
    adapter = VercelAIAdapterCustom(agent=agent, run_input=run_input, accept=accept)
    adapter.default_plan = PlanBlock.default("Analyzing your request")
    event_stream = adapter.run_encoded_sync(
        dep_builder=lambda send_stream: AgentContext(
            agent_conf=agent_conf, events=CustomUIEventSender(send_stream),
            thread=None,
            query="",
            parent_run=None
        ),
        message_history=message_history,
        on_complete=lambda run: on_complete(conversation_id, run),
    )

    return Response(
        event_stream,
        status=200,
        headers={
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Stream-Type": "limited",
        },
    )


@frappe.whitelist()
def run_a2ui():
    from pydantic_ai.ui.ag_ui import AGUIAdapter

    if not frappe.request.data:
        frappe.throw("Missing details to initiate a chat")
        return

    try:
        run_input = AGUIAdapter.build_run_input(frappe.request.data)
    except ValidationError:
        frappe.response["http_status_code"] = 422
        frappe.throw("Invalid Request Data")
        return

    # Load the message history
    conversation_id = run_input.id
    message_history = get_message_history(conversation_id)

    # Create a convertor which convert the model response to UIMessage responnse
    accept = frappe.request.headers.get("accept", SSE_CONTENT_TYPE)
    agent_conf, agent = build_rag_agent()
    adapter = AGUIAdapter(agent=agent, run_input=run_input, accept=accept)
    deps = AgentState(agent_conf=agent_conf)

    event_stream = adapter.run_stream(
        deps=deps,
        message_history=message_history,
        on_complete=lambda run: on_complete(conversation_id, run),
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


def get_message_history(conversation_id: str) -> AIConversation:
    conversation = frappe.get_doc("AI Conversation", conversation_id)
    if conversation.messages is not None:
        frappe.log("Message history loaded")
        return ModelMessagesTypeAdapter.validate_json(conversation.messages)

    frappe.log("No message history")
    return None


async def on_complete(conversation_id: str, run: AgentRun):
    conversation = frappe.get_doc("AI Conversation", conversation_id)
    save_history(conversation, run)
    frappe.db.commit()

    if not conversation.title == "New Chat":
        last_message = run.all_messages()[-1]
        conversation.title = last_message.text[:20]
        conversation.save()
    frappe.db.commit()


def save_history(converstion: AIConversation, run: AgentRun):
    messages_json = to_jsonable_python(run.all_messages_json())
    converstion.set_history(messages_json)
    converstion.save()


@frappe.whitelist()
def history():
    conversation_id = frappe.form_dict.get("conversation_id")
    conversation: AIConversation = frappe.get_doc("AI Conversation", conversation_id)
    conversation.check_permission("read")

    if conversation.messages is not None:
        message_history = ModelMessagesTypeAdapter.validate_json(conversation.messages)
        history = VercelAIAdapter.dump_messages(message_history)
        return to_jsonable_python(history)

    return []


@frappe.whitelist()
def history_a2ui():
    from pydantic_ai.ui.ag_ui import AGUIAdapter

    conversation_id = frappe.form_dict.get("conversation_id")
    conversation: AIConversation = frappe.get_doc("AI Conversation", conversation_id)
    if conversation.messages is not None:
        message_history = ModelMessagesTypeAdapter.validate_json(conversation.messages)
        history = AGUIAdapter.dump_messages(message_history)
        return to_jsonable_python(history)

    return []
