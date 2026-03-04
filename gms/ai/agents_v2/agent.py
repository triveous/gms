import queue
from typing import Any

import frappe
from deepagents import create_deep_agent
from langchain.agents.middleware.types import AgentState
from langchain_core.messages import HumanMessage, AIMessageChunk, ToolMessage
from langchain.tools import ToolRuntime
from langchain_core.runnables import RunnableConfig
from langgraph.config import get_stream_writer
from langgraph.types import Command
from pydantic_ai.ui.vercel_ai.response_types import (
    StartChunk,
    FinishChunk,
    BaseChunk,
    DataChunk,
    DoneChunk,
    TextStartChunk,
    TextDeltaChunk,
    TextEndChunk,
)
from typing import TypedDict
import asyncio

from gms.ai.kb.kb import Knowledge


class QueryKBStep(TypedDict):
    query: list[str]
    limit: int


class Source(TypedDict):
    name: str


class BrowseKBStep(TypedDict):
    sources: list[Source]


class StepBlock(TypedDict):
    steps: list[QueryKBStep | BrowseKBStep]


class UAgentState(AgentState):
    step: StepBlock


class VercelUIMessenger:
    started: bool
    ended: bool
    text_started: bool

    queue: queue.Queue

    def __init__(self):
        self.started = False
        self.ended = False
        self.text_started = False
        self.queue = queue.Queue()

    @staticmethod
    def encode(chunk: BaseChunk | str):
        content = chunk if isinstance(chunk, str) else chunk.encode()
        return f"data: {content}\n\n"

    def push_data(self, chunk: DataChunk | Any):
        if self.ended:
            return

        if not isinstance(chunk, DataChunk):
            return

        if not self.started:
            self.started = True
            self.queue.put(self.encode(StartChunk()))

        self.queue.put(self.encode(chunk))

    def push_text(self, id: str, text: str):
        if self.ended:
            return

        if not self.started:
            self.started = True
            self.queue.put(self.encode(StartChunk()))

        if not self.text_started:
            self.text_started = True
            self.queue.put(self.encode(TextStartChunk(id=id)))

        if text:
            self.queue.put(self.encode(TextDeltaChunk(id=id, delta=text)))
        else:
            self.queue.put(self.encode(TextEndChunk(id=id)))

    def finish(self):
        if self.ended:
            return

        self.ended = True
        self.queue.put(self.encode(FinishChunk()))
        self.queue.put(self.encode(DoneChunk()))

    def pull(self):
        if self.queue.empty():
            return None
        return self.queue.get()


_knowledge: Knowledge | None = None


def _get_knowledge() -> Knowledge:
    global _knowledge
    if _knowledge is None:
        settings = frappe.get_single("AI Settings")
        _knowledge = Knowledge(
            uri=settings.milvus_db_url,
            token=settings.milvus_db_token or "",
            collection_name=settings.milvus_kb_collection or "documents",
        )
    return _knowledge


def notify_search_query(query: list[str], runtime: ToolRuntime):
    writer = get_stream_writer()
    step_block: StepBlock | None = runtime.state.get("step")
    if step_block:
        step_block = step_block.copy()
        step_block["steps"].append(QueryKBStep(query=query, limit=20))
    else:
        step_block = StepBlock(steps=[QueryKBStep(query=query, limit=20)])
    writer(DataChunk(type="data-block", id="step", data=step_block))
    return step_block


def notify_browse(sources: list[str], runtime: ToolRuntime):
    writer = get_stream_writer()
    sources = [Source(name=s) for s in sources]
    step_block: StepBlock | None = runtime.state.get("step")
    if step_block:
        step_block = step_block.copy()
        step_block["steps"].append(BrowseKBStep(sources=sources))
    else:
        step_block = StepBlock(steps=[BrowseKBStep(sources=sources)])
    writer(DataChunk(type="data-block", id="step", data=step_block))
    return step_block


async def read_knowledge_base(query: list[str], runtime: ToolRuntime):
    """
    Reads and retrieves relevant content from the knowledge base based on the given query.

    Search for relevant documents in the knowledge base based on the given query.

    :param query: The user query to search the knowledge base.
    :type query: str
    :return: The retrieved chunk of content from document
    """

    knowledge = _get_knowledge()
    nested_results = await asyncio.gather(
        *[
            knowledge.asearch(
                q,
                limit=20,
                task_type="QUESTION_ANSWERING",
                output_fields=["text", "*"],
            )
            for q in query
        ]
    )
    results = [result for result_list in nested_results for result in result_list]
    content = "\n".join([f"<content>{result.text}</content>" for result in results])
    if len(results) == 0:
        return "Not content found for this. Try different query"
    return content


def create_gms_agent():
    return create_deep_agent(
        "google_genai:gemini-2.5-flash",
        tools=[read_knowledge_base],
        system_prompt="""
                You are AIKAM,  a helpful assistant answer only domain specific questions. Your domain is Grant Management.
                There are grant in the system. Each Grant will have project and there will be milestone update sharing planning information or
                progress information. Knowledgebase will contain everything about grant, but you cannot asumme there wil be explicit mention of
                word grant, though Project related words will be there

                Note: You should generate 1 todo at a time and complete it first before moving to another todo

                ### `read_knowledge_base` tool
                Use the read_knowledge_base tool to read the knowledge base and look for answer to any domain specific query those. You will generate
                upto 3 queries tacking the original query. Ensure that the query any self contained and doesn't need to know about previous conversation
                to understand the query
                Example:
                    Human: What is TANUH ?
                    AI : Use the read_knowledge_base tool to read the knowledge base and look for answer to any domain specific query those
                    Queries are TANUH, Tanuh Grant, Tanuh Projects, TANUH Milestones

                Example:
                    Human: What are the project in AICOE for Health?
                    AI : Since you don't know what is AICOE for Health, it is safe to assume that the query related knowledge might be in the knowledgebase.
                    Use the read_knowledge_base tool to read the knowledge base and look for answer. 
                    Queries are AICOE, Health AI, Projects in AICOE, 

                Example:
                    Human: What are all the projects
                    AI : Since you don't know what is the context, here you may prefer asking about which grant
                    Queries are Project in AICOE,  Project Cost in AICOE, Members in AICOE 

                Example:
                    Human: What is the size of sun compared to universe ?
                    AI : Denies answering since you are only responsible to answer domain specific query
                """,
    )


def run_gms_in_ui_mode(thread_id: str, run_id: str, query: str):
    agent = create_gms_agent()
    config: RunnableConfig = {
        "configurable": {"thread_id": thread_id, "run_id": run_id}
    }
    input = UAgentState(messages=[HumanMessage(content=query)])
    stream_mode = ["messages", "custom"]
    # noinspection PyTypeChecker

    ui_messenger = VercelUIMessenger()
    for stream_mode, chunk in agent.stream(input, config, stream_mode=stream_mode):
        if stream_mode == "custom":
            ui_messenger.push_data(chunk)
        if stream_mode == "messages":
            message_chunk, _ = chunk
            if isinstance(message_chunk, AIMessageChunk):
                for content in message_chunk.content_blocks:
                    if content.type == "text":
                        ui_messenger.push_text(
                            id=message_chunk.id, text=message_chunk.text
                        )

        while chunk := ui_messenger.pull():
            print(f"Chunk {chunk}")
            yield chunk

    ui_messenger.finish()
    while chunk := ui_messenger.pull():
        yield chunk


agent = create_gms_agent()
