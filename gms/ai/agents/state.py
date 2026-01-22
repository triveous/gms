from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal

from frappe.model.document import Document
from pydantic import BaseModel, Field

from gms.ai.agents.ui import CustomUIEventSender
from gms.ai.kb.knowledge_base import KnowledgeBase
from pydantic_ai.ui import StateDeps


class Todo(BaseModel):
    name: str
    status: Literal["pending", "in_progress", "completed"]


class PlanningState(BaseModel):
    todos: list[Todo] = Field(default_factory=list)


class Thought(BaseModel):
    title: str
    thought: str


class ThinkingState(BaseModel):
    thoughts: list[Thought] = Field(default_factory=list)
    thinking_started: datetime | None = None
    thoughts_duration: str = "Thought for 6s seconds"


@dataclass
class AgentState:
    agent_conf: Document
    events: CustomUIEventSender

    kb: KnowledgeBase = field(default_factory=KnowledgeBase)

    search_grant: str | None = None
    search_project: str | None = None
    search_project_milestone: str | None = None

    planning: PlanningState = field(default_factory=PlanningState)
    thinking: ThinkingState = field(default_factory=ThinkingState)

    sources: list[Document] = field(default_factory=list)


class Goal(BaseModel):
    id: str
    description: str
    final: bool
    pass


class IntialQueryContent(BaseModel):
    query: str


class SearchKBContent(BaseModel):
    class Query(BaseModel):
        query: str
        limit: str

    goal_id: str
    queries: list[Query]


class Source(BaseModel):
    name: str
    snippet: str
    metadata: dict[str, Any] | None = None
    is_from_kb: bool = Field(default=False)


class KBResultContent(BaseModel):
    goal_id: str
    kb_result: list[Source]


class Step(BaseModel):
    type: Literal["INTIAL_QUERY", "SEARCH_KB", "SEARCH_KB_RESULT"]
    id: str
    intial_query_content: IntialQueryContent | None = None
    search_kb_content: SearchKBContent | None = None
    kb_result_content: KBResultContent | None = None


class Block(BaseModel):
    type: Literal["PLAN", "STEP", "ASK_TEXT", "ASK_MARKDOWN", "SOURCES"]

    class State(BaseModel):
        pass


class PlanBlockState(Block.State):
    goals: list[Goal] = Field(default_factory=list)

    def add_goal(self, description: str):
        goal_id = len(self.add_goal)
        self.goals.append(Goal(id=str(goal_id), description=description))


class StepBlockState(Block.State):
    steps: list[Step] = Field(default_factory=list)
    progress: Literal["DEFAULT", "IN_PROGRESS", "DONE", "ERROR"] = Field(
        default="DEFAULT"
    )
    final: bool = False

    def add_intial_query_step(self, query: str):
        intial_query_step = Step(
            id="",
            type="INTIAL_QUERY",
            intial_query_content=IntialQueryContent(query=query),
        )
        self.steps.append(intial_query_step)

    def add_search_kb_step(self, goal_id: str, id: str, query: list[str], limit: int):
        queries = [SearchKBContent(query=q, limit=limit) for q in query]
        search_kb_step = Step(
            id=id,
            type="SEARCH_KB",
            search_kb_content=SearchKBContent(queries=queries, goal_id=goal_id),
        )
        self.steps.append(search_kb_step)

    def add_search_kb_result(
        self, goal_id: str, id: str, results: list[KBResultContent.Result]
    ):
        search_kb_result_step = Step(
            id=id,
            type="SEARCH_KB_RESULT",
            kb_result_content=KBResultContent(kb_result=results, goal_id=goal_id),
        )
        self.steps.append(search_kb_result_step)


class MarkdownBlockState(Block.State):
    progress: Literal["DEFAULT", "IN_PROGRESS", "DONE", "ERROR"]
    chunks: list[str]
    chunk_starting_offset: int = Field(default=0)
    answer: str


class AnswerSourceState(Block.State):
    sources: list[Source] = Field(default_factory=[])


class AgentRunState(BaseModel):
    blocks: list[Block] = Field(default_factory=[])


class AgentRun(StateDeps[AgentRunState]):
    kb: KnowledgeBase = field(default_factory=KnowledgeBase)
    state: AgentRunState
