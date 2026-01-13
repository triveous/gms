from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

from frappe.model.document import Document
from pydantic import BaseModel, Field

from gms.ai.agents.ui import CustomUIEventSender
from gms.ai.kb.knowledge_base import KnowledgeBase


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
