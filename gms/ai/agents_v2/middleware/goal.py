"""Middleware for generating and tracking agent goals.

This middleware enables the agent to define goals before and during execution,
providing an "internal monologue" that helps users understand the agent's
decision-making process. Goals are tracked as a list with a reducer pattern.

Features:
- Initial goal generated from user query in before_agent
- set_goal tool for agent to update goals during execution
- Goals linked to steps via goal_id (last goal in list is active)
"""

from typing import Annotated, Any, Literal

from langchain.agents.middleware import AgentMiddleware
from langchain.agents.middleware.types import AgentState, OmitFromInput
from langchain.tools import ToolRuntime
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage, AIMessage
from langchain_core.tools import StructuredTool
from langgraph.graph.state import Command
from pydantic import BaseModel, Field
from typing_extensions import TypedDict


# Default model for goal generation (lightweight/fast model)
DEFAULT_GOAL_MODEL = "google_genai:gemini-2.5-flash"

# System prompt for goal generation
GOAL_GENERATION_PROMPT = """You are helping to describe what an AI assistant is about to do.
Given the user's message, generate a very short goal description (3-5 words max) in simple layman terms.

Rules:
- Maximum 5 words
- Use simple, everyday language (no technical jargon)
- Start with an action verb (Finding, Searching, Looking, etc.)
- Be specific to what the user asked
- Don't use quotes or punctuation

Examples:
- "What grants are in AICOE?" → "Finding AICOE grants"
- "Tell me about project milestones" → "Looking up milestones"
- "How do I apply for funding?" → "Explaining funding process"

Respond with ONLY the goal text, nothing else."""

# Key used to store goals in message additional_kwargs
GOALS_PARTS_KEY = "goals_parts"


class GeneratedGoal(BaseModel):
    """Schema for structured goal generation output."""

    goal: str = Field(description="Short 3-5 word goal description")


# Goal status types
GoalStatus = Literal["active", "completed", "abandoned"]


class Goal(TypedDict, total=False):
    """A goal describing what the agent is about to do.

    Attributes:
        id: Unique identifier for this goal
        text: Short description (3-5 words) of the goal
        status: Current status of the goal
    """

    id: str
    text: str
    status: GoalStatus


def goals_reducer(existing: list[Goal] | None, new: list[Goal] | None) -> list[Goal]:
    """Custom reducer for goals field that merges by goal ID.

    - If a goal with the same ID exists, it gets updated
    - If a goal ID is new, it gets appended
    - Order is preserved based on first appearance

    Args:
        existing: Current goals list (may be None on first call)
        new: New goals to merge in

    Returns:
        Merged list of goals
    """
    if existing is None:
        existing = []
    if new is None:
        return existing

    # Build a dict for fast lookup, preserving order
    goals_by_id: dict[str, Goal] = {}
    for goal in existing:
        goal_id = goal.get("id")
        if goal_id:
            goals_by_id[goal_id] = goal

    # Merge new goals
    for goal in new:
        goal_id = goal.get("id")
        if goal_id:
            if goal_id in goals_by_id:
                # Update existing goal
                goals_by_id[goal_id] = {**goals_by_id[goal_id], **goal}
            else:
                # Add new goal
                goals_by_id[goal_id] = goal

    return list(goals_by_id.values())


SET_GOAL_TOOL_DESCRIPTION = """Set a new goal describing what you're about to do.
Call this tool when:
- Starting a new approach or strategy
- Changing direction after getting stuck
- Breaking down a complex task into sub-goals

The goal should be 3-5 simple words describing your next action.

Examples:
- "Searching project data"
- "Trying different query"
- "Looking for grant details"
"""


def create_set_goal_tool():
    """Create the set_goal tool for agents to update their goal."""

    def set_goal(goal_text: str, runtime: ToolRuntime) -> Command:
        """Set a new goal for the current task.

        Args:
            goal_text: Short 3-5 word description of the new goal
            runtime: Tool runtime context

        Returns:
            Command updating goals in state
        """
        # Clean up goal text
        goal_text = goal_text.strip()
        if len(goal_text) > 50:
            goal_text = goal_text[:47] + "..."

        # Get next sequential ID from current goals count
        existing_goals = runtime.state.get("goals", [])
        next_id = str(len(existing_goals))

        # Create new goal with sequential ID
        new_goal = Goal(
            id=next_id,
            text=goal_text,
            status="active",
        )

        print(f"Agent set new goal: {goal_text}")

        # Stream goal to UI
        try:
            from gms.ai.agents_v2.utils.ui_stream_writer import get_ui_stream_writer

            writer = get_ui_stream_writer()
            writer.write_goal(new_goal)
        except Exception as e:
            print(f"Failed to stream goal: {e}")

        # Return command to update state
        return Command(
            update={
                "messages": [
                    ToolMessage(
                        content=f"Goal set: {goal_text}",
                        tool_call_id=runtime.tool_call_id,
                    )
                ],
                "goals": [new_goal],
            }
        )

    return StructuredTool.from_function(
        func=set_goal,
        name="set_goal",
        description=SET_GOAL_TOOL_DESCRIPTION,
    )


class GoalState(AgentState):
    """Extended state with goals list. Last goal in list is the active goal."""

    goals: Annotated[list[Goal], goals_reducer, OmitFromInput]


class GoalMiddleware(AgentMiddleware[GoalState, Any]):
    """Middleware that generates goals and provides set_goal tool.

    This middleware creates an "internal monologue" by:
    1. Generating an initial goal from the user's query (before_agent)
    2. Providing a set_goal tool for the agent to update goals during execution

    Goals are tracked as a list with a reducer, and steps can link to goals
    via goal_id to show which step was done for which goal.

    Usage:
        agent = create_deep_agent(
            ...
            middleware=[GoalMiddleware()],
        )

    Args:
        model: Model to use for goal generation (defaults to gemini-2.5-flash)
        prompt: Custom system prompt for goal generation
    """

    state_schema = GoalState

    def __init__(
        self,
        model: str | BaseChatModel | None = None,
        prompt: str | None = None,
    ):
        super().__init__()
        self.model = model or DEFAULT_GOAL_MODEL
        self.prompt = prompt or GOAL_GENERATION_PROMPT
        self.set_goal_tool = create_set_goal_tool()
        self.tools = [self.set_goal_tool]

    def before_agent(self, state: GoalState, runtime: Any) -> dict[str, Any] | None:
        """Generate initial goal before the agent starts processing.

        Uses the last human message to generate a short goal description.
        Streams the goal to the UI via UIStreamWriter.

        Args:
            state: Current agent state with messages
            runtime: Agent runtime context

        Returns:
            State update with goals, or None if generation fails
        """
        # Don't generate if we already have goals (resuming conversation)
        existing_goals = state.get("goals", [])
        if existing_goals:
            return None

        try:
            goal = self._generate_initial_goal(state)
            if goal:
                print(f"Generated initial goal: {goal['text']}")

                # Stream goal to UI
                self._stream_goal(goal)

                return {
                    "goals": [goal],
                }
        except Exception as e:
            # Don't fail the agent if goal generation fails
            print(f"Goal generation failed: {e}")

        return None

    def after_agent(self, state: GoalState, runtime: Any) -> dict[str, Any] | None:
        """Persist goals to the last message's additional_kwargs."""
        messages = state.get("messages", [])
        goals = state.get("goals", [])

        if not messages or not goals:
            return None

        # Get the last AI message
        for msg in reversed(messages):
            if isinstance(msg, AIMessage):
                # Ensure additional_kwargs exists
                if not hasattr(msg, "additional_kwargs"):
                    msg.additional_kwargs = {}

                # Persist goals
                # We persist all goals in the list so the UI can reconstruct the history
                msg.additional_kwargs[GOALS_PARTS_KEY] = goals
                break

        return None

    def _generate_initial_goal(self, state: GoalState) -> Goal | None:
        """Generate initial goal from the last human message.

        Args:
            state: Agent state containing messages

        Returns:
            Goal dict or None if generation fails
        """
        messages = state.get("messages", [])
        if not messages:
            return None

        # Get the last human message
        user_message = None
        for msg in reversed(messages):
            if getattr(msg, "type", None) == "human":
                user_message = getattr(msg, "content", "")
                break

        if not user_message:
            return None

        # Initialize model with streaming disabled
        from langchain.chat_models import init_chat_model

        if isinstance(self.model, str):
            model = init_chat_model(self.model, disable_streaming=True)
        else:
            model = self.model

        # Generate goal using structured output
        structured_model = model.with_structured_output(GeneratedGoal)

        result = structured_model.invoke(
            [
                SystemMessage(content=self.prompt),
                HumanMessage(content=f"User message: {user_message}"),
            ]
        )

        if result and result.goal:
            # Clean up the goal
            goal_text = result.goal.strip()
            if len(goal_text) > 50:
                goal_text = goal_text[:47] + "..."

            # Initial goal always gets ID 0
            return Goal(
                id="0",
                text=goal_text,
                status="active",
            )

        return None

    def _stream_goal(self, goal: Goal) -> None:
        """Stream the goal to the UI.

        Args:
            goal: The generated goal to stream
        """
        try:
            from gms.ai.agents_v2.utils.ui_stream_writer import get_ui_stream_writer

            writer = get_ui_stream_writer()
            writer.write_goal(goal)
        except Exception as e:
            # Don't fail if streaming fails
            print(f"Failed to stream goal: {e}")
