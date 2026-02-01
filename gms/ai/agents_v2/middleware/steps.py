"""Steps middleware for tracking query progress.

This middleware adds a `steps` field to the agent's state schema,
enabling tools to track and update step progress (e.g., "searching KB",
"reading file"). Uses a custom reducer for proper merging by step ID.
"""

from typing import Annotated, Any, Literal

from langchain.agents import AgentState
from langchain.agents.middleware import AgentMiddleware
from langchain.agents.middleware.types import OmitFromInput
from typing_extensions import TypedDict


# Step progress states
StepProgress = Literal["in-progress", "done", "error"]


class Step(TypedDict, total=False):
    """A single step in the agent's execution flow.

    Attributes:
        id: Unique identifier for this step
        type: Step type (e.g., "search_kb", "read_file", "browse")
        content: Type-specific content (e.g., {"query": [...]})
        progress: Current progress state
    """

    id: str
    type: str
    content: dict[str, Any]
    progress: StepProgress


class SearchKBContent(TypedDict, total=False):
    """Content for search_kb step type."""

    query: list[str]
    results_count: int


class SearchKBStep(TypedDict, total=False):
    """Step for knowledge base search operations."""

    id: str
    type: Literal["search_kb"]
    content: SearchKBContent
    progress: StepProgress


class BrowseKBContent(TypedDict, total=False):
    """Content for browse_kb step type."""

    sources: list[str]


class BrowseKBStep(TypedDict, total=False):
    """Step for browsing knowledge base sources."""

    id: str
    type: Literal["browse_kb"]
    content: BrowseKBContent
    progress: StepProgress


def steps_reducer(existing: list[Step] | None, new: list[Step] | None) -> list[Step]:
    """Custom reducer for steps field that merges by step ID.

    - If a step with the same ID exists, it gets updated
    - If a step ID is new, it gets appended
    - Order is preserved based on first appearance

    Args:
        existing: Current steps list (may be None on first call)
        new: New steps to merge in

    Returns:
        Merged list of steps
    """
    if existing is None:
        existing = []
    if new is None:
        return existing

    # Build a dict for fast lookup, preserving order
    steps_by_id: dict[str, Step] = {}
    for step in existing:
        step_id = step.get("id")
        if step_id:
            steps_by_id[step_id] = step

    # Merge new steps
    for step in new:
        step_id = step.get("id")
        if step_id:
            if step_id in steps_by_id:
                # Update existing step
                steps_by_id[step_id] = {**steps_by_id[step_id], **step}
            else:
                # Add new step
                steps_by_id[step_id] = step

    return list(steps_by_id.values())


class StepsState(AgentState):
    """State extension that includes steps field.

    The steps field tracks progress through agent execution.
    Uses a custom reducer to merge updates by step ID.
    """

    steps: Annotated[list[Step], steps_reducer, OmitFromInput]


class StepsMiddleware(AgentMiddleware[StepsState, Any]):
    """Middleware that adds steps field to agent state schema.

    This middleware enables tools to track step progress via Command returns.
    Steps are merged using steps_reducer by step ID.

    Usage:
        from gms.ai.agents_v2.middleware.steps import StepsMiddleware

        agent = create_deep_agent(
            ...,
            middleware=[StepsMiddleware()],
        )

    Tools can then return:
        return Command(
            update={
                "messages": [ToolMessage(...)],
                "steps": [{"id": "search", "type": "search_kb", "progress": "done"}],
            }
        )
    """

    state_schema = StepsState
    tools = []  # No additional tools
