from __future__ import annotations

from deepagents import SubAgent, create_deep_agent
from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import BaseCheckpointSaver

from gms.ai.agents_v2.checkpointer.frappe_in import FrappeBufferedCheckpointer
from gms.ai.kb.kb import Knowledge
from gms.ai.agents_v2.middleware.kb_search import KBSearchMiddleware
from gms.ai.agents_v2.middleware.steps import StepsMiddleware, Step
from gms.ai.agents_v2.middleware.title_generation import TitleGenerationMiddleware
from gms.ai.agents_v2.middleware.state_sync import (
    EndStateNotifierMiddleware,
    StartStateNotifierMiddleware,
)
from gms.ai.agents_v2.vercel_ui.stream_handler import VercelUIStreamHandler
from gms.ai.agents_v2.vercel_ui.converter import (
    convert_messages_to_ui_messages,
    UI_DATA_PARTS_KEY,
)


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

    # StepsMiddleware adds steps to state schema for both SubAgent and main agent
    # This enables tools to update steps via Command, which propagates up
    research_agent = SubAgent(
        name="research-agent",
        model=SUB_AGENT_DEFAULT_MODEL,
        description="Research agent",
        system_prompt=RESEARCH_AGENT_SYSTEM_PROMPT,
        tools=[],
        middleware=[
            StepsMiddleware(),  # Enable steps in SubAgent state
            KBSearchMiddleware(knowledge=knowledge),
        ],
    )

    return create_deep_agent(
        model=model,
        system_prompt=system_prompt,
        checkpointer=checkpointer,
        subagents=[research_agent],
        middleware=[
            EndStateNotifierMiddleware(),  # Register FIRST to run LAST in after_agent (reverse)
            StepsMiddleware(),  # Enable steps in main agent state
            TitleGenerationMiddleware(),  # Generate title before/after agent
            StartStateNotifierMiddleware(),  # Register LAST to run LAST in before_agent
        ],
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


def _apply_steps_to_last_message(messages: list, steps: list[Step]) -> None:
    """
    Apply collected steps to the last AIMessage's additional_kwargs.

    This persists the steps with the message so it's available
    when loading chat history.
    """
    if not steps:
        return

    # Find the last AIMessage
    for msg in reversed(messages):
        if isinstance(msg, (AIMessage, AIMessageChunk)):
            # Merge with existing
            existing = msg.additional_kwargs.get(UI_DATA_PARTS_KEY, {})
            if existing:
                existing_parts = existing.get("data_parts", [])
                steps = existing_parts + steps

            msg.additional_kwargs[UI_DATA_PARTS_KEY] = {"data_parts": steps}
            break


def run_chat_agent_ui_mode(knowledge: Knowledge, thread_id: str, query: str):
    config: RunnableConfig = {"configurable": {"thread_id": thread_id}}
    checkpointer = FrappeBufferedCheckpointer()
    checkpointer.load_from_frappe(config)

    agent = create_chat_agent(knowledge, checkpointer=checkpointer)
    # Use plain dict - StepsMiddleware provides the state schema with steps
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

    # Get final state and apply steps to last message
    final_state = agent.get_state(config)
    messages = final_state.values.get("messages", [])
    steps = final_state.values.get("steps", [])
    print(f"Steps: {steps}")

    _apply_steps_to_last_message(messages, steps)
    print(f"Message{messages[-1]}")

    # Update state with modified messages so steps are persisted
    if steps:
        agent.update_state(config, {"messages": messages})

    checkpointer.flush_to_frappe()
