from typing import Any

from langchain.agents import AgentState
from langchain.agents.middleware import AgentMiddleware
from langchain_core.messages import AIMessage, AIMessageChunk, ToolMessage


# Key used to store tasks in message additional_kwargs  (mirrors STEPS_PARTS_KEY)
TASK_PARTS_KEY = "tasks_parts"


class TaskMiddleware(AgentMiddleware[AgentState, Any]):
    """Middleware that persists tasks to the last AIMessage.

    This middleware ensures tasks are available when loading chat history by
    moving task IDs from ToolMessage additional_kwargs to the parent AIMessage.
    """

    state_schema = AgentState
    tools = []  # No additional tools

    def after_agent(self, state: AgentState, runtime: Any) -> dict[str, Any] | None:
        """Persist tasks to the AIMessage after agent completes.

        It looks for ToolMessages that contain a 'task_id' in additional_kwargs,
        and adds them to the TASK_PARTS_KEY of the AIMessage that made the call.
        """
        messages = state.get("messages", [])
        if not messages:
            return None

        # Map tool_call_id to task_id from ToolMessages
        task_map: dict[str, str] = {}
        for msg in messages:
            if isinstance(msg, ToolMessage):
                task_id = msg.additional_kwargs.get("task_id")
                if task_id:
                    task_map[msg.tool_call_id] = task_id

        if not task_map:
            return None

        # Attach task info to the AIMessages that made the tool calls
        updated = False
        for msg in messages:
            if isinstance(msg, (AIMessage, AIMessageChunk)):
                if not hasattr(msg, "tool_calls"):
                    continue

                for tc in msg.tool_calls:
                    tc_id = tc.get("id")
                    if tc_id in task_map:
                        task_id = task_map[tc_id]
                        existing = msg.additional_kwargs.get(TASK_PARTS_KEY, [])
                        
                        # Add if not already present
                        if not any(t.get("id") == task_id for t in existing):
                            existing.append({
                                "id": task_id,
                                "status": "Submitting"  # Initial state
                            })
                            msg.additional_kwargs[TASK_PARTS_KEY] = existing
                            updated = True

        return {"messages": messages} if updated else None


