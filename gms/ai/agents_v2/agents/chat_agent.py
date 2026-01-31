from typing import Annotated, Any

from deepagents import SubAgent, create_deep_agent
from langchain.agents import AgentState
from langchain.agents.middleware.types import OmitFromInput
from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import BaseCheckpointSaver

from gms.ai.agents_v2.checkpointer.frappe_in import FrappeBufferedCheckpointer
from gms.ai.kb.kb import Knowledge
from gms.ai.agents_v2.middleware.kb_search import KBSearchMiddleware
from gms.ai.agents_v2.vercel_ui.stream_handler import VercelUIStreamHandler
from gms.ai.agents_v2.vercel_ui.converter import (
    convert_messages_to_ui_messages,
    UI_DATA_PARTS_KEY,
)
from gms.ai.agents_v2.utils.ui_stream_writer import ui_data_reducer


# Custom state for chat agent with UI data support
class ChatAgentState(AgentState):
    """
    Extended agent state that tracks UI data for persistence.

    The ui_data field collects non-transient data from UIStreamWriter
    and is merged using a custom reducer to prevent overwriting.
    It's marked OmitFromInput so it doesn't pollute the input schema.
    """

    ui_data: Annotated[dict[str, Any], ui_data_reducer, OmitFromInput]


DEFAULT_SYSTEM_PROMPT = """You are AIKAM, a helpful assistant answer only domain specific questions. Your domain is Grant Management.
There are grant in the system. Each Grant will have project and there will be milestone update sharing planning information or
progress information. Knowledgebase will contain everything about grant, but you cannot assume there wil be explicit mention of
word grant, though Project related words will be there

Prefer using research using research-agent when unknown domain specific query is asked 
Example: What are the project in AICOE for Health?
"""

DEFAULT_MODEL = "google_genai:gemini-2.5-pro"
SUB_AGENT_DEFAULT_MODEL = "google_genai:gemini-2.5-flash"
RESEARCH_AGENT_SYSTEM_PROMPT = """You are research agent specially designed-purpose agent for researching complex questions, \
searching for content on knowledgebase, and executing multi-step tasks. When you are searching for a keyword and are not \
confident that you will find the right match in the first few tries use this agent to perform the search for you. \
This agent has access to all tools as the main agent.

You have access to read_knowledge_base tool to search for content on knowledgebase
"""


def create_chat_agent(
    knowledge: Knowledge,
    checkpointer: BaseCheckpointSaver | None = None,
):
    """Create a chat agent with knowledge base search capability.

    Args:
        knowledge: Knowledge instance for searching the knowledge base
        checkpointer: Optional checkpointer for state persistence
    """
    model: str = DEFAULT_MODEL
    system_prompt: str = DEFAULT_SYSTEM_PROMPT

    research_agent = SubAgent(
        name="research-agent",
        model=SUB_AGENT_DEFAULT_MODEL,
        description="Research agent",
        system_prompt=RESEARCH_AGENT_SYSTEM_PROMPT,
        tools=[],
        middleware=[KBSearchMiddleware(knowledge=knowledge)],
    )
    return create_deep_agent(
        model=model,
        system_prompt=system_prompt,
        checkpointer=checkpointer,
        subagents=[research_agent],
    )


def get_chat_agent_history(knowledge: Knowledge, thread_id: str):
    config: RunnableConfig = {"configurable": {"thread_id": thread_id}}
    checkpointer = FrappeBufferedCheckpointer()
    checkpointer.load_from_frappe(config)

    agent = create_chat_agent(knowledge, checkpointer=checkpointer)
    state = agent.get_state(config)
    messages = state.values.get("messages", [])
    ui_messages = convert_messages_to_ui_messages(messages)
    return ui_messages


def _apply_ui_data_to_last_message(messages: list, ui_data: dict[str, Any]) -> None:
    """
    Apply collected UI data to the last AIMessage's additional_kwargs.

    This persists the UI data with the message so it's available
    when loading chat history.
    """
    if not ui_data:
        return

    # Find the last AIMessage
    for msg in reversed(messages):
        if isinstance(msg, (AIMessage, AIMessageChunk)):
            # Convert ui_data dict to list of parts
            parts = list(ui_data.values())

            # Merge with existing
            existing = msg.additional_kwargs.get(UI_DATA_PARTS_KEY, {})
            if existing:
                existing_parts = existing.get("data_parts", [])
                parts = existing_parts + parts

            msg.additional_kwargs[UI_DATA_PARTS_KEY] = {"data_parts": parts}
            break


def run_chat_agent_ui_mode(knowledge: Knowledge, thread_id: str, query: str):
    config: RunnableConfig = {"configurable": {"thread_id": thread_id}}
    checkpointer = FrappeBufferedCheckpointer()
    checkpointer.load_from_frappe(config)

    agent = create_chat_agent(knowledge, checkpointer=checkpointer)
    state = ChatAgentState(messages=[HumanMessage(content=query)])

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

    # Get final state and apply ui_data to last message
    final_state = agent.get_state(config)
    messages = final_state.values.get("messages", [])
    ui_data = final_state.values.get("ui_data", {})

    _apply_ui_data_to_last_message(messages, ui_data)

    checkpointer.flush_to_frappe()
