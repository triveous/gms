from dataclasses import dataclass, field
from typing import Literal

from frappe.model.document import Document
from pydantic import BaseModel

from gms.ai.kb.knowledge_base import KnowledgeBase


class Todo(BaseModel):
    name: str
    status: Literal["pending", "in_progress", "completed"]


class PlanningState:
    todos: list[Todo] = field(default_factory=list)


@dataclass
class AgentState:
    agent_conf: Document
    kb = KnowledgeBase()
    search_grant: str = None
    search_project: str = None
    search_project_milestone: str = None
    planning: PlanningState = PlanningState()
    sources: list[Document] = field(default_factory=list)
