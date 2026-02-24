from datetime import datetime
from typing import TYPE_CHECKING

from deepagents import SubAgent, create_deep_agent
from langchain.tools import ToolRuntime
from langchain_core.messages import HumanMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import StructuredTool
from langgraph.checkpoint.base import BaseCheckpointSaver

from gms.ai.agents_v2.checkpointer.frappe_in import FrappeBufferedCheckpointer

if TYPE_CHECKING:
    from gms.ai.doctype.ai_agent.ai_agent import AIAgent
from gms.ai.agents_v2.middleware.data_overview import DataOverviewMiddleware
from gms.ai.agents_v2.middleware.goal import GoalMiddleware
from gms.ai.agents_v2.middleware.kb_search import KBSearchMiddleware
from gms.ai.agents_v2.middleware.state_sync import (
    EndStateNotifierMiddleware,
    StartStateNotifierMiddleware,
)
from gms.ai.agents_v2.middleware.steps import StepsMiddleware
from gms.ai.agents_v2.middleware.task import TaskMiddleware
from gms.ai.agents_v2.middleware.title_generation import TitleGenerationMiddleware
from gms.ai.agents_v2.vercel_ui.converter import convert_messages_to_ui_messages
from gms.ai.agents_v2.vercel_ui.stream_handler import VercelUIStreamHandler
from gms.ai.kb.kb import Knowledge

DEFAULT_SYSTEM_PROMPT = """You are AIKAM, a helpful assistant answer only domain specific questions. Your domain is Grant Management.
There are grant in the system. Each Grant will have project and there will be milestone update sharing planning information or
progress information. Knowledgebase will contain everything about grant, but you cannot assume there wil be explicit mention of
word grant, though Project related words will be there

Prefer using research using research-agent when unknown domain specific query is asked 
Example: What are the project in AICOE for Health?

You shouldn't tell you don't know. These can be very domain specific term. You will treat that you don't have enough. And when you don't have enough information, delegate the task to specific sub_agent to do it for you
Example: What is tanuh
This is very specific internal name of grant which you won't know, It's better to delegate to sub agent which can give you this information
So basically whenver you don't know or you are not sure even partially about any topic, delegate to a sub_agent

"""

DEFAULT_MODEL = "google_genai:gemini-2.5-pro"
SUB_AGENT_DEFAULT_MODEL = "google_genai:gemini-2.5-flash"
RESEARCH_AGENT_SYSTEM_PROMPT = """You are research agent specially designed-purpose agent for researching complex questions, \
searching for content on knowledgebase, and executing multi-step tasks. When you are searching for a keyword and are not \
confident that you will find the right match in the first few tries use this agent to perform the search for you. \
This agent has access to all tools as the main agent.

You can use the data_overview tool to understand what information are available to the user. Whenever you start the research you call this to know what information you have
to make better research. 
Example: User asked query about tell me everything about TANUH.
Since you are search from a knowledge base, you query won't always give all the information. So how do you know there are something missing. That's why you need to call this first to know what information are available
This will help you define the research better.

You have access to read_knowledge_base tool to search for content on knowledgebase

Whenever you are tacking a new part of the research you should call the set_goal to define your research area. This is so that user know what you are doing. Whateve goal is define, it is shown to the user. So avoid adding technical/internal details
"""


def _request_file_upload(runtime: "ToolRuntime"):
    """Request the user to upload a document/file for extraction. Call this tool when the user expresses intent to upload a file."""
    import frappe
    from langgraph.config import get_stream_writer
    from langgraph.types import Command

    doc = frappe.new_doc("Grant Document Extraction Task")
    doc.status = "Submitting"
    doc.insert(ignore_permissions=True)
    frappe.db.commit()

    task_id = doc.name

    data_payload = {"task": task_id, "status": "Submitting"}

    writer = get_stream_writer()
    if writer:
        writer({"type": "data-task", "id": task_id, "data": data_payload})

    frappe.publish_realtime("data-task", data_payload)

    # Persist task to agent state so TaskMiddleware.after_agent() stores it in
    # AIMessage.additional_kwargs[TASK_PARTS_KEY] – identical to how
    # StepsMiddleware handles data-steps.
    return Command(
        update={
            "tasks": [{"id": task_id, "status": "Submitting", "data": data_payload}],
            "messages": [
                ToolMessage(
                    content=f"Created Grant Document Extraction Task '{task_id}'. Awaiting user file upload. Tell the user you have opened the file upload prompt.",
                    tool_call_id=runtime.tool_call_id,
                )
            ],
        }
    )


request_file_upload = StructuredTool.from_function(
    func=_request_file_upload,
    name="request_file_upload",
    description="Request the user to upload a document/file for extraction. Call this tool when the user expresses intent to upload a file.",
)


def create_chat_agent(
    ai_agent_id: str,
    knowledge: Knowledge,
    checkpointer: BaseCheckpointSaver | None = None,
):
    """Create a chat agent with knowledge base search capability.

    Args:
        ai_agent_id: ID of the AI Agent document containing configuration
        knowledge: Knowledge instance for searching the knowledge base
        checkpointer: Optional checkpointer for state persistence
    """
    import frappe

    # Load AI Agent document using cached_doc (prevents loading every time)
    ai_agent: AIAgent = frappe.get_cached_doc("AI Agent", "ulfovrcs4m")

    # Use agent configuration or fallback to defaults
    model: str = ai_agent.model or DEFAULT_MODEL
    system_prompt: str = ai_agent.instruction or DEFAULT_SYSTEM_PROMPT
    # Append current time to system prompt
    system_prompt += f"\n\nCurrent Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    # Build sub-agents from the AI Agent's agents child table
    subagents = []
    for sub_agent_row in ai_agent.agents or []:
        # Load the linked AI Agent document (cached)
        sub_ai_agent: AIAgent = frappe.get_cached_doc("AI Agent", sub_agent_row.agent)

        # Build middleware list for this sub-agent based on its flags
        sub_middleware = []
        if sub_ai_agent.steps_middleware:
            sub_middleware.append(StepsMiddleware())
        if sub_ai_agent.goal_middleware:
            sub_middleware.append(GoalMiddleware())
        if sub_ai_agent.data_overview:
            sub_middleware.append(DataOverviewMiddleware())
        if sub_ai_agent.kb_search_middleware:
            sub_middleware.append(
                KBSearchMiddleware(
                    knowledge=knowledge,
                    search_limit=sub_ai_agent.kb_search_top_k or 10,
                    search_max_result=sub_ai_agent.kb_search_max_result_count or 50,
                )
            )

        # Prepare sub-agent system prompt with current time
        sub_system_prompt = sub_ai_agent.instruction or ""
        sub_system_prompt += (
            f"\n\nCurrent Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

        # Create SubAgent with configuration from the linked AI Agent
        subagent = SubAgent(
            name=sub_agent_row.tool_name,
            model=sub_ai_agent.model or SUB_AGENT_DEFAULT_MODEL,
            description=sub_agent_row.tool_description,
            system_prompt=sub_system_prompt,
            tools=[],
            middleware=sub_middleware,
        )
        subagents.append(subagent)

    # Build main agent middleware list based on flags
    main_middleware = []
    main_middleware.append(
        EndStateNotifierMiddleware()
    )  # Register FIRST to run LAST in after_agent
    if ai_agent.steps_middleware:
        main_middleware.append(StepsMiddleware())
    if ai_agent.goal_middleware:
        main_middleware.append(GoalMiddleware())
    main_middleware.append(TaskMiddleware())  # Always register – data-task must always persist
    if ai_agent.title_middleware:
        main_middleware.append(
            TitleGenerationMiddleware(
                model=ai_agent.title_model or None,
                prompt=ai_agent.title_prompt or None,
            )
        )
    main_middleware.append(
        StartStateNotifierMiddleware()
    )  # Register LAST to run LAST in before_agent

    return create_deep_agent(
        name=ai_agent.agent_name,
        model=model,
        system_prompt=system_prompt,
        checkpointer=checkpointer,
        subagents=subagents,
        middleware=main_middleware,
        tools=[request_file_upload],
    )


def get_chat_agent_history(knowledge: Knowledge, thread_id: str):
    config: RunnableConfig = {"configurable": {"thread_id": thread_id}}
    checkpointer = FrappeBufferedCheckpointer()
    checkpointer.load_from_frappe(config)

    agent = create_chat_agent(knowledge, checkpointer=checkpointer)
    state = agent.get_state(config)
    messages = state.values.get("messages", [])
    print(f"History message {messages[-1]}")
    ui_messages = convert_messages_to_ui_messages(messages)
    return ui_messages


def run_chat_agent_ui_mode(knowledge: Knowledge, thread_id: str, query: str):
    """Run chat agent in UI mode with SSE streaming.

    Note: Steps persistence is handled by StepsMiddleware.after_agent,
    so no manual step handling is needed here.
    """
    config: RunnableConfig = {"configurable": {"thread_id": thread_id}}
    checkpointer = FrappeBufferedCheckpointer()
    checkpointer.load_from_frappe(config)

    agent = create_chat_agent(knowledge, checkpointer=checkpointer)
    state = {"messages": [HumanMessage(content=query)]}

    handler = VercelUIStreamHandler()

    # Start stream
    yield from handler.start()

    # Process agent stream
    for _, stream_mode, data in agent.stream(
        state,
        config,
        stream_mode=["messages", "custom"],
        subgraphs=True,
    ):
        yield from handler.process_event(stream_mode, data)

    # Finish stream
    yield from handler.finish()

    # Flush checkpointer data
    checkpointer.flush_to_frappe()
