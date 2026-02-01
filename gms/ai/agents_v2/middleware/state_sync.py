"""Middleware for syncing agent state to frontend.

This middleware runs before and after the agent completes and sends the full state
(except messages) to the frontend as a transient data event.
"""

from typing import Any

from langchain.agents.middleware import AgentMiddleware
from langchain.agents.middleware.types import AgentState
from langgraph.config import get_config


class StateNotifierMiddleware(AgentMiddleware[AgentState, Any]):
    """Middleware that sends agent state to frontend before and after execution.

    This middleware uses the `before_agent` and `after_agent` hooks to send the
    complete state (excluding messages) to the frontend. This includes:
    - thread_id (from config)
    - thread_title (if generated)
    - ui_data (UI state accumulated during execution)

    The data is sent as a transient 'data-state' event, meaning it's
    streamed to the frontend but not persisted in the message history.

    Usage:
        agent = create_deep_agent(
            ...
            middleware=[
                TitleGenerationMiddleware(),
                StateNotifierMiddleware(),  # Should be last middleware
            ],
        )
    """

    def before_agent(self, state: AgentState, runtime: Any) -> dict[str, Any] | None:
        """Send current state to frontend before agent proceeds.

        Args:
            state: Current agent state
            runtime: Agent runtime context

        Returns:
            None - only streams data, doesn't update state
        """
        self._send_state(state, phase="before")
        return None

    def after_agent(self, state: AgentState, runtime: Any) -> dict[str, Any] | None:
        """Send state to frontend after agent completes.

        Args:
            state: Current agent state
            runtime: Agent runtime context

        Returns:
            None - only streams data, doesn't update state
        """
        self._send_state(state, phase="after")
        return None

    def _send_state(self, state: AgentState, phase: str) -> None:
        """Send state to frontend.

        Args:
            state: Current agent state
            phase: Either "before" or "after" to identify when state was sent
        """
        try:
            # Get thread_id from config
            config = get_config()
            thread_id = config.get("configurable", {}).get("thread_id")

            # Build state payload (everything except messages)
            state_payload = {
                "thread_id": thread_id,
                "thread_title": state.get("thread_title"),
                "ui_data": state.get("ui_data"),
            }

            # Stream state to frontend
            from gms.ai.agents_v2.utils.ui_stream_writer import get_ui_stream_writer

            writer = get_ui_stream_writer()
            writer.write_data(
                data_type="state",
                payload=state_payload,
                transient=True,
            )
            print(f"Streamed state ({phase}): thread_id={thread_id}")

        except Exception as e:
            # Don't fail the agent if state sync fails
            print(f"State sync failed ({phase}): {e}")
