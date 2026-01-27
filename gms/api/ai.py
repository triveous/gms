import frappe
from frappe import _
from gms.ai.doctype.ai_thread.ai_thread import AIThread
from werkzeug.wrappers import Response
from gms.ai.agents.ui import stream_async_iterator
from pydantic_ai import TextPart, UserPromptPart
from pydantic_ai.ui import MessagesBuilder
from gms.ai.agents_v2.builder import build_agent
from gms.ai.agents_v2.state import AgentContext
import asyncio


@frappe.whitelist()
def ask():
    """
    Return the realtime events for a thread run
    """
    query = frappe.form_dict.get("query")
    if not query:
        frappe.throw(_("Missing Query"))
        return
    # This can be None meaning this is first time  user is asking any query in the thread
    thread_id = frappe.form_dict.get("thread_id")
    # Id of the last run which the user requested the last time which can be None when this is first time
    # user is requested
    parent_run_id = frappe.form_dict.get("parent_run_id")

    return Response(
        runner_sync(thread_id=thread_id, parent_run_id=parent_run_id, query=query),
        status=200,
        headers={
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Stream-Type": "limited",
        },
    )


def runner_sync(thread_id: str | None, parent_run_id: str | None, query: str):
    return stream_async_iterator(runner(thread_id, parent_run_id, query))


# Build RAG agent
def build_rag_agent():
    rag_agent_name = frappe.get_single_value("GMS Settings", "rag_agent")
    agent_conf = frappe.get_doc("AI Agent", rag_agent_name)
    return agent_conf, build_agent(agent_conf)


def runner(thread_id: str | None, parent_run_id: str, query: str):
    is_new_thread, thread = get_thread(thread_id)
    message_history = (
        []
        if is_new_thread
        else get_message_history(
            thread_id=thread_id, parent_run_id=parent_run_id or thread.last_run
        )
    )
    conf, agent = build_rag_agent()

    async def stream_generator():
        context = AgentContext()
        response = context.get_response()

        run_coroutine = agent.run(
            query,
            message_history=message_history,
            deps=context,
        )

        # FIX: Use asyncio.create_task instead of create_task_group.
        # This schedules the runner on the loop without binding it
        # to the specific Task ID of the first chunk's execution.
        runner_task = asyncio.create_task(run_coroutine)

        try:
            async for event in response:
                yield event
              
        except Exception as e:
            print(e)
            # If the WSGI client disconnects or an error occurs reading,
            # cancel the runner to prevent orphaned tasks.
            runner_task.cancel()
            raise

        # Optional: Await the runner to propagate any exceptions that happened inside it
        # If the stream finished normally, this will return immediately.
        try:
            await runner_task
        except Exception as e:
            print(e)
            raise

    return stream_generator()


def get_thread(thread_id: str | None) -> tuple[bool, AIThread]:
    if not thread_id:
        # Return true if a new thread is created along with the thread
        return True, frappe.new_doc("AI Thread")

    thread = frappe.get_doc("AI Thread", thread_id)
    if not thread:
        raise frappe.throw(_("Invalid thread"))

    # Returns False when an existing thread is fetched
    return False, thread


def get_message_history(thread_id: str, parent_run_id: str | None):
    if not parent_run_id:
        frappe.log("Parent Run not giving. Ignoring history")
        return []

    # Enforce permission check
    runs = frappe.get_all("AI Thread Run", {"thread": thread_id})

    if len(runs) == 0:
        frappe.log("No previous run found")
        return []

    # When there is no run or the parent id is missing, ignore history
    if parent_run_id not in [r["name"] for r in runs]:
        frappe.log(_("Invalid parent run"))
        return []

    historical_runs = sorted(runs, key=lambda x: x["creation"])
    # distinct generator to find the first matching index
    cutoff_historical_runs_index = next(
        i for i, d in enumerate(historical_runs) if d.get("name") == parent_run_id
    )
    valid_runs = historical_runs[: cutoff_historical_runs_index + 1]
    return run_to_messages(valid_runs)


def run_to_messages(runs):
    message_builder = MessagesBuilder()
    for run in runs:
        message_builder.add(UserPromptPart(run["query"]))
        message_builder.add(TextPart(run["answer"]))

    return message_builder.messages
