from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal

from frappe.model.document import Document
from pydantic import BaseModel, Field
from pydantic_ai.ui.vercel_ai.response_types import DataChunk

from gms.ai.agents.ui import CustomUIEventSender
from gms.ai.kb.knowledge_base import KnowledgeBase
import uuid
from pydantic import TypeAdapter


class Todo(BaseModel):
    name: str
    status: Literal["pending", "in_progress", "completed"]


class PlanningState(BaseModel):
    todos: list[Todo] = Field(default_factory=list)


class Thought(BaseModel):
    title: str = Field(description="3 4 word description of thought")
    thought: str = Field(
        description="Your throught on what you have understood and what you should do. Avoid using anything technincal and any mention of any tool or how will you achieve it internally. User doesn't need to know what tools you posses. Keep it within. 10 wor"
    )


class ThinkingState(BaseModel):
    thoughts: list[Thought] = Field(default_factory=list)
    thinking_started: datetime | None = None
    thoughts_duration: str = "Thought for 6s seconds"


@dataclass
class AgentState:
    agent_conf: Document
    events: CustomUIEventSender

    kb: KnowledgeBase = field(default_factory=KnowledgeBase)
    planning: PlanningState = field(default_factory=PlanningState)
    thinking: ThinkingState = field(default_factory=ThinkingState)

    sources: list[Document] = field(default_factory=list)


######### UTILS

BlockType = Literal["plan", "step", "ask_text"]


class Block(BaseModel):
    class Content(BaseModel):
        pass

    usage: BlockType


class Source(BaseModel):
    name: str


class SearchQuery(BaseModel):
    query: str
    limit: int


######### PLAN #########


class Goal(BaseModel):
    id: str
    description: str
    final: bool
    pass


class PlanBlock(Block):
    class Content(Block.Content):
        goals: list[Goal] = Field(default_factory=list)

        def get_content_fields(self):
            return {"goals": self.goals}

        def add_goal(self, description: str):
            goal_id = len(self.add_goal)
            self.goals.append(Goal(id=str(goal_id), description=description))

    usage: BlockType = "plan"
    plan_content: Content = Field(default_factory=Content)

    def default(text: str):
        return PlanBlock(
            plan_content=PlanBlock.Content(
                goals=[Goal(description=text, id="0", final=True)]
            )
        )


######### PLAN #########


######### STEP #########
class IntialQueryStep(BaseModel):
    class Content(BaseModel):
        query: str

    id: str = ""
    type: Literal["INITIAL_QUERY"] = "INITIAL_QUERY"
    intial_query: Content


class KBSearchStep(BaseModel):
    class Content(BaseModel):
        goal_id: str
        queries: list[SearchQuery]

    id: str
    type: Literal["KB_SEARCH"] = "KB_SEARCH"
    kb_search: Content


class BrowseKBResultStep(BaseModel):
    class Content(BaseModel):
        goal_id: str
        sources: list[Source]

    id: str
    type: Literal["BROWSE_KB_RESULT"] = "BROWSE_KB_RESULT"
    browse_kb_result: Content


Steps = IntialQueryStep | KBSearchStep | BrowseKBResultStep


class StepBlockContent(Block.Content):
    steps: list[Steps] = Field(default_factory=list)
    progress: Literal["DEFAULT", "IN_PROGRESS", "DONE", "ERROR"] = Field(
        default="DEFAULT"
    )
    final: bool = False


class StepBlock(Block):
    usage: BlockType = "step"
    step_content: StepBlockContent = Field(default_factory=StepBlockContent)

    def add_step(self, step: Steps):
        steps = self.step_content.steps
        steps.append(step)
        self.step_content.steps = steps

    def add_intial_query_step(self, query: str):
        intial_query_step = IntialQueryStep(
            intial_query=IntialQueryStep.Content(query=query),
        )
        self.add_step(intial_query_step)

    def add_kb_search_step(self, goal_id: str, id: str, queries: list[str], limit: int):
        queries = [SearchQuery(query=q, limit=limit) for q in queries]
        search_kb_step = KBSearchStep(
            id=id,
            kb_search=KBSearchStep.Content(
                queries=queries,
                goal_id=goal_id,
            ),
        )
        self.add_step(search_kb_step)

    def add_browse_kb_result_step(self, goal_id: str, id: str, sources: list[Source]):
        browser_kb_result_step = BrowseKBResultStep(
            id=id,
            browse_kb_result=BrowseKBResultStep.Content(
                sources=sources,
                goal_id=goal_id,
            ),
        )
        self.add_step(browser_kb_result_step)


######### STEP #########


######### ASK TEXT RESULT #########
class MarkdownBlockContent(Block.Content):
    progress: Literal["DEFAULT", "IN_PROGRESS", "DONE", "ERROR"] = Field(
        default="DEFAULT"
    )
    chunks: list[str] = Field(default_factory=list)
    chunk_starting_offset: int = Field(default=0)
    answer: str | None = Field(default=None)


class AskResultBlock(Block):
    usage: BlockType = "ask_text"
    answer_markdown_content: MarkdownBlockContent = Field(
        default_factory=MarkdownBlockContent
    )


######### ASK TEXT RESULT #########


######### ANSWER SOURCE #########
class AnswerSourceContent(BaseModel):
    sources: list[Source] = Field(default_factory=[])


class AnswerSourceBlock(Block):
    usage: BlockType = "ask_text"
    answer_source_content: AnswerSourceContent


######### ANSWER SOURCE #########

AllBlock = PlanBlock | StepBlock | AskResultBlock


@dataclass
class AgentRunState:
    blocks: list[Block] = field(default_factory=list)

    def to_json(self):
        return TypeAdapter(list[AllBlock]).dump_json(self.blocks).decode()

    def step(self) -> StepBlock:
        for b in self.blocks:
            if b.usage == "step":
                return b
        block = StepBlock()
        self.blocks.append(block)
        return block

    def plan(self) -> PlanBlock:
        for b in self.blocks:
            if b.usage == "plan":
                return b
        block = PlanBlock()
        self.blocks.append(block)
        return block

    def ask_result(self) -> AskResultBlock:
        for b in self.blocks:
            if b.usage == "ask_text":
                return b
        block = AskResultBlock()
        self.blocks.append(block)
        return block


@dataclass
class AgentContext:
    agent_conf: Document
    query: str
    thread: Any
    parent_run: Any

    events: CustomUIEventSender

    kb: KnowledgeBase = field(default_factory=KnowledgeBase)
    planning: PlanningState = field(default_factory=PlanningState)
    thinking: ThinkingState = field(default_factory=ThinkingState)

    sources: list[Document] = field(default_factory=list)

    statew: AgentRunState = field(default_factory=AgentRunState)

    async def add_kb_search_step(self, queries: list[str], limit: int, goal_id="0"):
        step_block = self.statew.step()
        step_block.add_kb_search_step(
            goal_id,
            id=str(uuid.uuid4()),
            queries=queries,
            limit=limit,
        )
        await self.send_block_update([step_block])

    async def add_browse_kb_result_step(self, sources: list[str], goal_id="0"):
        if len(sources) == 0:
            return

        step_block = self.statew.step()
        step_block.add_browse_kb_result_step(
            goal_id,
            id=str(uuid.uuid4()),
            sources=[Source(name=s) for s in set(sources)],
        )
        await self.send_block_update([step_block])

    def add_answer(self, answer: str):
        ask_result_block = self.statew.ask_result()
        ask_result_block.answer_markdown_content.progress = "DONE"
        ask_result_block.answer_markdown_content.chunks = [answer]
        ask_result_block.answer_markdown_content.answer = answer
        return ask_result_block

    async def send_block_update(self, blocks: list[Block]):
        for block in blocks:
            await self.events.send_event(
                DataChunk(
                    type="data-block",
                    id=block.usage,
                    data=block.model_dump(),
                )
            )
