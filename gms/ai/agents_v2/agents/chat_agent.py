from deepagents import SubAgent, create_deep_agent
from langchain.agents import AgentState
from langchain_core.messages import AIMessageChunk, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import BaseCheckpointSaver

from gms.ai.agents_v2.checkpointer.frappe_in import FrappeBufferedCheckpointer
from gms.ai.kb.kb import Knowledge
from gms.ai.agents_v2.middleware.kb_search import KBSearchMiddleware

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


def run_chat_agent_ui_mode(knowledge: Knowledge, thread_id: str, query: str):
    config: RunnableConfig = {"configurable": {"thread_id": thread_id}}
    checkointer = FrappeBufferedCheckpointer()
    checkointer.load_from_frappe(config)

    agent = create_chat_agent(knowledge, checkpointer=checkointer)
    state = AgentState(messages=[HumanMessage(content=query)])

    # noinspection PyTypeChecker
    try:
        for event in agent.stream(
            state, config, stream_mode=["messages", "custom"], subgraphs=True
        ):
            _, stream_mode, data = event
            if stream_mode == "messages":
                ai_message, checkpoint = data
                if isinstance(ai_message, AIMessageChunk):
                    for content in ai_message.content_blocks:
                        if content["type"] == "text":
                            yield "data: " + content["text"] + "\n\n"

    except Exception as e:
        import traceback

        traceback.print_exception(e)
        yield f"data: {str(e)}\n\n"

    finally:
        state = agent.get_state(config)
        checkointer.get(config)
        checkointer.flush_to_frappe()
