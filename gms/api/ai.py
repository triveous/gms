import frappe
from frappe import ValidationError, _
from gms.ai.agents.state import AgentContext
from gms.ai.agents.ui import CustomUIEventSender
from gms.ai.doctype.ai_thread.ai_thread import AIThread
from gms.api.conversation import VercelAIAdapterCustom
from werkzeug.wrappers import Response
from pydantic_ai import TextPart, UserPromptPart
from pydantic_ai.ui import MessagesBuilder, SSE_CONTENT_TYPE
from gms.ai.agents.builder import build_agent
from pydantic_ai import RunContext, Agent, AgentRunResult
from pydantic import BaseModel, Field


# Build RAG agent
def build_rag_agent():
    rag_agent_name = frappe.get_single_value("GMS Settings", "rag_agent")
    agent_conf = frappe.get_doc("AI Agent", rag_agent_name)
    return agent_conf, build_agent(agent_conf)


@frappe.whitelist()
def ask():
    if not frappe.request.data:
        frappe.throw("Missing details to initiate a chat")
        return

    try:
        run_input = VercelAIAdapterCustom.build_run_input(frappe.request.data)
        if len(run_input.messages) == 0:
            frappe.throw("Missing query")
            return
    except ValidationError:
        frappe.response["http_status_code"] = 422
        frappe.throw("Invalid Request Data")
        return

    query = run_input.messages[-1].parts[0].text
    if not query:
        frappe.response["http_status_code"] = 400
        frappe.throw("Missing Query")
        return

    thread_id = run_input.id
    thread = get_thread(thread_id)
    parent_run, message_history = get_message_history(thread_id)

    # Create a convertor which convert the model response to UIMessage responnse
    accept = frappe.request.headers.get("accept", SSE_CONTENT_TYPE)

    # Ensure that we have a running loop, Agent internally create an HTTP Client which uses event loop
    # Then when we create event loop for event stream, it probably replace the event loop.
    # Now wer are creating the http.AsycnClient in the agent builder, so we need to ensure that there is a running loop before that
    VercelAIAdapterCustom.set_loop()

    agent_conf, agent = build_rag_agent()
    adapter = VercelAIAdapterCustom(agent=agent, run_input=run_input, accept=accept)
    event_stream = adapter.run_encoded_sync(
        dep_builder=lambda send_stream: AgentContext(
            agent_conf=agent_conf,
            events=CustomUIEventSender(send_stream),
            query=query,
            thread=thread,
            parent_run=parent_run,
        ),
        message_history=message_history,
        on_start=lambda ctx: on_start(ctx),
        on_complete=lambda ctx, result: on_complete(ctx, result),
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


async def on_start(ctx: AgentContext):
    if ctx.thread.has_default_title():
        print("Generating title")

        class GenerateTitle(BaseModel):
            title: str = Field(description="title of the conversation")

        agent = Agent(
            model=ctx.agent_conf.model,
            system_prompt="Summarize the ai conversation in 5 words of fewer",
            output_type=GenerateTitle,
        )
        response = await agent.run("<conversation>Human: {query} </conversation")
        ctx.thread.title = response.output.title
    ctx.thread.save()
    frappe.db.commit()


def on_complete(ctx: AgentContext, result: AgentRunResult):
    try:
        thread_run = frappe.new_doc(
            "AI Thread Run",
            thread=ctx.thread.name,
            query=ctx.query,
            answer="Some Answer",
            blocks="[]",
        )
        thread_run.insert()
        ctx.thread.last_run = thread_run.name
        ctx.thread.save()
        frappe.db.commit()
        print("ON Complete")
    except Exception as e:
        print(e)


def get_thread(thread_id: str | None) -> tuple[bool, AIThread]:
    if not thread_id:
        # Return true if a new thread is created along with the thread
        return frappe.new_doc("AI Thread")

    thread = frappe.get_doc("AI Thread", thread_id)
    if not thread:
        raise frappe.throw(_("Invalid thread"))

    # Returns False when an existing thread is fetched
    return thread


def get_message_history(thread_id: str | None):
    if not thread_id:
        frappe.log("Parent Run not giving. Ignoring history")
        return None, []

    # Enforce permission check
    runs = frappe.get_all("AI Thread Run", {"thread": thread_id})

    if len(runs) == 0:
        frappe.log("No previous run found")
        return None, []

    historical_runs = sorted(runs, key=lambda x: x["creation"])
    return historical_runs[-1], run_to_messages(historical_runs)


def run_to_messages(runs):
    message_builder = MessagesBuilder()
    for run in runs:
        message_builder.add(UserPromptPart(run["query"]))
        message_builder.add(TextPart(run["answer"]))

    return message_builder.messages
