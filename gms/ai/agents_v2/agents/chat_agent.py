from __future__ import annotations

from deepagents import SubAgent, create_deep_agent
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import BaseCheckpointSaver

from gms.ai.agents_v2.checkpointer.frappe_in import FrappeBufferedCheckpointer
from gms.ai.agents_v2.middleware.data_overview import DataOverviewMiddleware
from gms.ai.agents_v2.middleware.goal import GoalMiddleware
from gms.ai.agents_v2.middleware.kb_search import KBSearchMiddleware
from gms.ai.agents_v2.middleware.state_sync import (
    EndStateNotifierMiddleware,
    StartStateNotifierMiddleware,
)
from gms.ai.agents_v2.middleware.steps import StepsMiddleware
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
            GoalMiddleware(),  # Generate goal before agent starts
            DataOverviewMiddleware(),
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
            GoalMiddleware(),  # Generate goal before agent starts
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
