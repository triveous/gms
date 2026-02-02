"""
UI Stream Writer utility for LangGraph agents.

Provides a simple wrapper around LangGraph's get_stream_writer for
streaming UI data chunks to the frontend.
"""

from typing import TYPE_CHECKING, Any, Callable

from langgraph.config import get_stream_writer

if TYPE_CHECKING:
    from gms.ai.agents_v2.middleware.steps import Step
    from gms.ai.agents_v2.middleware.goal import Goal


def get_ui_stream_writer() -> "UIStreamWriter":
    """
    Get a UIStreamWriter instance with the internal stream writer pre-loaded.

    This is the recommended way to create a UIStreamWriter in tools/middleware,
    as it ensures the stream writer is ready to use immediately.

    Returns:
        UIStreamWriter instance with stream writer initialized.

    Example:
        from gms.ai.agents_v2.utils import get_ui_stream_writer

        def my_tool(query: str):
            writer = get_ui_stream_writer()
            writer.write_step(SearchKBStep(
                id="search",
                type="search_kb",
                content={"query": query},
                progress="in-progress",
            ))
    """
    writer = UIStreamWriter()
    writer._ensure_writer()  # Pre-load the stream writer
    return writer


class UIStreamWriter:
    """
    A simple stream writer wrapper for sending UI data chunks.

    Wraps LangGraph's get_stream_writer and provides convenience methods
    for streaming step updates and other data to the frontend.

    Usage in a tool:
        from gms.ai.agents_v2.utils import get_ui_stream_writer
        from gms.ai.agents_v2.middleware.steps import SearchKBStep

        def my_tool(query: str):
            writer = get_ui_stream_writer()

            # Write step progress
            step = SearchKBStep(
                id="search",
                type="search_kb",
                content={"query": query},
                progress="in-progress",
            )
            writer.write_step(step)

            # ... do work ...

            # Update step progress
            step["progress"] = "done"
            writer.write_step(step)
    """

    def __init__(self):
        """Initialize the UI stream writer."""
        self._stream_writer: Callable | None = None

    def _ensure_writer(self) -> Callable:
        """Lazily get the stream writer."""
        if self._stream_writer is None:
            self._stream_writer = get_stream_writer()
        return self._stream_writer

    def write(self, data: dict[str, Any]) -> None:
        """
        Write data directly to the stream.

        Args:
            data: The data to write. Should have a "type" key.
        """
        writer = self._ensure_writer()
        writer(data)

    def write_step(self, step: "Step") -> None:
        """
        Write a step update to the stream.

        Sends a data-step chunk with the step data.

        Args:
            step: Step instance (or subtype like SearchKBStep, BrowseKBStep)

        Example:
            from gms.ai.agents_v2.middleware.steps import SearchKBStep

            writer.write_step(SearchKBStep(
                id="search_kb",
                type="search_kb",
                content={"query": ["test"]},
                progress="in-progress",
            ))
        """
        step_id = step.get("id", "")
        data: dict[str, Any] = {
            "type": "data-step",
            "id": step_id,
            "data": dict(step),
        }
        self.write(data)

    def write_goal(self, goal: "Goal") -> None:
        """
        Write a goal update to the stream.

        Sends a data-goal chunk with the goal data.

        Args:
            goal: Goal instance
        """
        goal_id = goal.get("id", "")
        data: dict[str, Any] = {
            "type": "data-goal",
            "id": goal_id,
            "data": dict(goal),
        }
        self.write(data)

    def write_data(
        self, data_type: str, payload: Any, data_id: str | None = None
    ) -> None:
        """
        Write custom data to the stream.

        Args:
            data_type: Type name (will be prefixed with "data-" if needed)
            payload: The data payload
            data_id: Optional ID for the data
        """
        if not data_type.startswith("data-"):
            data_type = f"data-{data_type}"

        data: dict[str, Any] = {
            "type": data_type,
            "data": payload,
        }
        if data_id:
            data["id"] = data_id
        self.write(data)
