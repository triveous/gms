import frappe
from frappe import ValidationError, _
from gms.ai.agents.builder import build_agent
from gms.ai.agents.state import AgentContext, Goal, PlanBlock
from gms.ai.agents.ui import CustomUIEventSender
from gms.ai.agents_v2.agent_runner import AgentRunner
from gms.ai.doctype.ai_thread.ai_thread import AIThread
from gms.api.conversation import VercelAIAdapterCustom
from pydantic import BaseModel, Field
from pydantic_ai import Agent, AgentRunResult, TextPart, UserPromptPart
from pydantic_ai.ui import SSE_CONTENT_TYPE, MessagesBuilder
from pydantic_core import to_jsonable_python
from werkzeug.wrappers import Response


# Build RAG agent
def build_rag_agent():
    rag_agent_name = frappe.get_single_value("GMS Settings", "rag_agent")
    agent_conf = frappe.get_doc("AI Agent", rag_agent_name)
    return agent_conf, build_agent(agent_conf)


@frappe.whitelist()
def ask2():
    """Run chat agent in UI mode with SSE streaming."""
    thread_id = frappe.form_dict.get("thread_id")
    query = frappe.form_dict.get("query")

    if not query:
        frappe.throw("Missing query")
        return

    runner = AgentRunner(thread_id)

    return Response(
        runner.run_ui_mode(query),
        status=200,
        headers={
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Stream-Type": "limited",
        },
    )


@frappe.whitelist()
def history2():
    """Get chat history for a thread."""
    thread_id = frappe.form_dict.get("thread_id")

    if not thread_id:
        frappe.throw("Missing thread")
        return

    runner = AgentRunner(thread_id)
    return runner.get_history()


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
    runner = AgentRunner(thread_id)

    return Response(
        runner.run_ui_mode(query),
        status=200,
        headers={
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Stream-Type": "limited",
        },
    )


async def on_start(ctx: AgentContext):
    pass


def generate_title(ctx: AgentContext, result: AgentRunResult):
    if ctx.thread.has_default_title():
        print("Generating title")

        class GenerateTitle(BaseModel):
            title: str = Field(description="title of the conversation")

        custom_prompt = frappe.db.get_single_value(
            "AI Settings", "conversation_title_generation_prompt"
        )
        agent = Agent(
            model=ctx.agent_conf.model,
            system_prompt=custom_prompt
            or "Summarize the ai conversation in 5 words of fewer",
            output_type=GenerateTitle,
        )
        response = agent.run_sync(
            f"<conversation>{result.all_messages_json()}</conversation"
        )
        ctx.thread.title = response.output.title
        ctx.thread.save()
        frappe.db.commit()


def on_complete(ctx: AgentContext, result: AgentRunResult):
    try:
        # Save the thread first
        ctx.thread.save()
        frappe.db.commit()

        add_thread_run(ctx, result)

        # Update the first answer of the thread for quick access
        if not ctx.thread.first_answer:
            ctx.thread.first_answer = result.output
            ctx.thread.save()
            frappe.db.commit()

        generate_title(ctx, result)
    except Exception as e:
        print(e)


def add_thread_run(ctx: AgentContext, result: AgentRunResult):
    # # App answer to state
    ctx.add_answer(result.output)

    blocks_json = ctx.statew.to_json()
    print(f"Block sjon {blocks_json}")

    thread_run = frappe.new_doc(
        "AI Thread Run",
        thread=ctx.thread.name,
        query=ctx.query,
        answer=result.output,
        blocks=blocks_json,
    )
    thread_run.save()

    # Quick access for the last run
    ctx.thread.last_run = thread_run
    ctx.thread.save()

    frappe.db.commit()
    return thread_run


def get_thread(thread_id: str | None) -> tuple[bool, AIThread]:
    if not thread_id:
        # Return true if a new thread is created along with the thread
        return frappe.new_doc("AI Thread")

    thread = frappe.get_doc("AI Thread", thread_id)
    thread.check_permission()
    if not thread:
        raise frappe.throw(_("Invalid thread"))

    # Returns False when an existing thread is fetched
    return thread


@frappe.whitelist()
def history():
    thread_id = frappe.form_dict.get("thread_id")

    if not thread_id:
        frappe.throw("Missing thread")
        return

    runner = AgentRunner(thread_id)
    return runner.get_history()


def get_message_history(thread_id: str | None):
    if not thread_id:
        frappe.log("Parent Run not giving. Ignoring history")
        return None, []

    # Enforce permission check
    runs = frappe.get_all(
        "AI Thread Run",
        filters={"thread": thread_id},
        fields=["query", "answer"],
        order_by="creation asc",
    )

    if len(runs) == 0:
        frappe.log("No previous run found")
        return None, []

    return runs[-1], run_to_messages(runs)


def run_to_messages(runs):
    message_builder = MessagesBuilder()
    for run in runs:
        message_builder.add(UserPromptPart(run["query"]))
        message_builder.add(TextPart(run["answer"]))

    return message_builder.messages
