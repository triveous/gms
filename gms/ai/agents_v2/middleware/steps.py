"""Steps middleware for tracking query progress.

This middleware adds a `steps` field to the agent's state schema,
enabling tools to track and update step progress (e.g., "searching KB",
"reading file"). Uses a custom reducer for proper merging by step ID.
"""

from typing import Annotated, Any, Literal

from langchain.agents import AgentState
from langchain.agents.middleware import AgentMiddleware
from langchain_core.messages import AIMessage, AIMessageChunk
from typing_extensions import TypedDict


# Key used to store steps in message additional_kwargs
STEPS_PARTS_KEY = "steps_parts"

# Step progress states
StepProgress = Literal["in-progress", "done", "error"]


class Step(TypedDict, total=False):
    """A single step in the agent's execution flow.

    Attributes:
        id: Unique identifier for this step
        type: Step type (e.g., "search_kb", "read_file", "browse")
        goal_id: ID of the goal this step is linked to
        content: Type-specific content (e.g., {"query": [...]})
        progress: Current progress state
    """

    id: str
    type: str
    goal_id: str | None
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
    goal_id: str | None
    content: SearchKBContent
    progress: StepProgress


class BrowseKBSource(TypedDict, total=False):
    """A source document in browse_kb step."""

    id: str  # ai_document_id
    title: str  # filename
    page: int


class BrowseKBContent(TypedDict, total=False):
    """Content for browse_kb step type."""

    sources: list[BrowseKBSource]


class BrowseKBStep(TypedDict, total=False):
    """Step for browsing knowledge base sources."""

    id: str
    type: Literal["browse_kb"]
    goal_id: str | None
    content: BrowseKBContent
    progress: StepProgress


class Replace(list):
    """Wrapper to signal 'replace entirely' instead of merge in reducers.

    Use this when you want to clear/reset a reducer-managed field:
        return {"steps": Replace([])}  # Clears steps
        return {"steps": Replace([new_step])}  # Replaces with new list
    """

    pass


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

    # If new is a Replace wrapper, replace entirely
    if isinstance(new, Replace):
        return list(new)

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

    steps: Annotated[list[Step], steps_reducer]


class StepsMiddleware(AgentMiddleware[StepsState, Any]):
    """Middleware that adds steps field to agent state schema.

    This middleware enables tools to track step progress via Command returns.
    Steps are merged using steps_reducer by step ID.

    The after_agent hook persists steps to the last AIMessage so they
    are available when loading chat history.

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

    def after_agent(self, state: StepsState, runtime: Any) -> dict[str, Any] | None:
        """Persist steps to the last AIMessage after agent completes.

        This ensures steps are available when loading chat history by
        storing them in the message's additional_kwargs.

        Args:
            state: Current agent state containing steps and messages
            runtime: Agent runtime context

        Returns:
            Updated state with steps attached to last message, or None if no steps
        """
        steps = state.get("steps", [])
        if not steps:
            return None

        messages = state.get("messages", [])
        if not messages:
            return None

        # Find the last AIMessage
        for msg in reversed(messages):
            if isinstance(msg, (AIMessage, AIMessageChunk)):
                # Get existing steps if any
                existing = msg.additional_kwargs.get(STEPS_PARTS_KEY, [])
                if existing:
                    # Merge with existing steps using reducer logic
                    steps = steps_reducer(existing, steps)

                msg.additional_kwargs[STEPS_PARTS_KEY] = steps
                break

        # Return updated messages
        return {"messages": messages}
