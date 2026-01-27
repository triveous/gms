from typing import TypedDict

from pydantic import BaseModel, Field
from typing_extensions import Literal

from gms.ai.kb.knowledge_base import KnowledgeBase


# ------------- REDUCER
def manage_blocks(current: list, update: list | dict) -> list:
    """
    Reducer to manage blocks list using 'type' as the unique key.
    - List update: Appends new blocks.
    - Dict update: Updates existing block by 'type' or appends if missing.
    """
    if not current:
        current = []

    # Standard append if the update is a list
    if isinstance(update, list):
        return current + update

    # Update logic using 'type' property
    if isinstance(update, dict) and "type" in update:
        new_state = current.copy()
        update_type = update["type"]

        for i, block in enumerate(new_state):
            if block.get("type") == update_type:
                # Merge existing block with the update
                new_state[i] = {**block, **update}
                return new_state

        # If type not found, append as a new block
        return current + [update]

    return current


# -------------
# . COMMON
class SearchQuery(BaseModel):
    query: str
    limit: int


class Source(BaseModel):
    name: str
    snippet: str


class ClassfierResult(BaseModel):
    skipSearch: bool = Field(description="Indicates whether to skip the search step")
    personalSearch: bool = Field(
        description="Indicates whether to perform a personal search"
    )


class PreQueryDecider(BaseModel):
    classifier_result: ClassfierResult
    standaloneFollowUp: str = Field(
        "A self-contained, context-independent reformulation of the user's question."
    )


# -------------------- BLOCK --------------------
class Block(BaseModel):
    type: Literal["PLAN", "STEP"]

    class Content(BaseModel):
        pass

    pass


# ----------------- PLAN BLOCK -------------------
class Goal(BaseModel):
    id: str
    final: bool
    description: str


class PlanBlock(Block):
    class Content(Block.Content):
        goals: list[Goal]

    plan_content: Content


# ----------------- PLAN BLOCK -------------------


# ----------------- STEP BLOCK -------------------
class BaseStep(BaseModel):
    id: str


class IntialQueryStep(BaseStep):
    id: str = ""

    class Content(BaseModel):
        query: str

    type: Literal["INTIAL_QUERY"]
    initial_query: Content


class KBSearchStep(BaseStep):
    class Content(BaseModel):
        goal_id: str
        queries: list[SearchQuery]

    type: Literal["KB_SEARCH"]
    kb_search: Content


class BrowseKBResultStep(BaseStep):
    class Content(BaseModel):
        goal_id: str
        sources: list[Source]

    type: Literal["BROWSE_KB_RESULT"]
    browse_kb_result: Content


Step = IntialQueryStep | KBSearchStep | BrowseKBResultStep


class StepBlock(Block):
    class Content(Block.Content):
        steps: list[Step] = Field(default_factory=list)
        progress: Literal["DEFAULT", "IN_PROGRESS", "DONE", "ERROR"] = "DONE"
        final: bool = False

    type: Literal["STEP"] = "STEP"
    step_content: Content


# ----------------- STEP BLOCK -------------------
class AgentState(BaseModel):
    query: str
    convesation_history: str = ""
    classifier_result: ClassfierResult | None = None
    blocks: list[PlanBlock | StepBlock] = Field(default_factory=list)


class AgentContext(TypedDict):
    kb: KnowledgeBase
