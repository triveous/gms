"""Task middleware for tracking file upload / extraction task state.

This middleware adds a `tasks` field to the agent's state schema,
enabling tools to store data-task events. Uses a custom reducer so
tasks are merged by task `id`.

The after_agent hook persists tasks to the last AIMessage so they
are available when loading chat history – exactly how StepsMiddleware
handles `data-steps`.
"""

from typing import Annotated, Any

from langchain.agents import AgentState
from langchain.agents.middleware import AgentMiddleware
from langchain_core.messages import AIMessage, AIMessageChunk
from typing_extensions import TypedDict


# Key used to store tasks in message additional_kwargs  (mirrors STEPS_PARTS_KEY)
TASK_PARTS_KEY = "tasks_parts"


class Task(TypedDict, total=False):
    """A single data-task entry.

    Attributes:
        id:     Unique identifier for this task record (e.g. Frappe docname)
        status: Current status string (e.g. "Submitting", "Validating", …)
        data:   Arbitrary extra payload attached to the task event
    """

    id: str
    status: str
    data: dict[str, Any]


def tasks_reducer(existing: list[Task] | None, new: list[Task] | None) -> list[Task]:
    """Custom reducer for tasks field that merges by task ID.

    - If a task with the same ID exists, it gets updated.
    - If a task ID is new, it gets appended.
    - Order is preserved based on first appearance.
    """
    if existing is None:
        existing = []
    if new is None:
        return existing

    # Build a dict for fast lookup, preserving order
    tasks_by_id: dict[str, Task] = {}
    for task in existing:
        task_id = task.get("id")
        if task_id:
            tasks_by_id[task_id] = task

    # Merge new tasks
    for task in new:
        task_id = task.get("id")
        if task_id:
            if task_id in tasks_by_id:
                tasks_by_id[task_id] = {**tasks_by_id[task_id], **task}
            else:
                tasks_by_id[task_id] = task

    return list(tasks_by_id.values())


class TasksState(AgentState):
    """State extension that includes tasks field.

    The tasks field tracks data-task events (file upload / extraction tasks).
    Uses a custom reducer to merge updates by task ID.
    """

    tasks: Annotated[list[Task], tasks_reducer]


class TaskMiddleware(AgentMiddleware[TasksState, Any]):
    """Middleware that adds tasks field to agent state schema.

    This middleware enables tools to track data-task events via Command returns.
    Tasks are merged using tasks_reducer by task ID.

    The after_agent hook persists tasks to the last AIMessage so they
    are available when loading chat history.

    Usage:
        from gms.ai.agents_v2.middleware.task import TaskMiddleware

        agent = create_deep_agent(
            ...,
            middleware=[TaskMiddleware()],
        )

    Tools can then return:
        return Command(
            update={
                "messages": [ToolMessage(...)],
                "tasks": [{"id": task_id, "status": "Submitting"}],
            }
        )
    """

    state_schema = TasksState
    tools = []  # No additional tools

    def after_agent(self, state: TasksState, runtime: Any) -> dict[str, Any] | None:
        """Persist tasks to the last AIMessage after agent completes.

        This ensures tasks are available when loading chat history by
        storing them in the message's additional_kwargs.

        Args:
            state: Current agent state containing tasks and messages
            runtime: Agent runtime context

        Returns:
            Updated state with tasks attached to last message, or None if no tasks
        """
        tasks = state.get("tasks", [])
        if not tasks:
            return None

        messages = state.get("messages", [])
        if not messages:
            return None

        # Find the last AIMessage
        for msg in reversed(messages):
            if isinstance(msg, (AIMessage, AIMessageChunk)):
                # Get existing tasks if any and merge
                existing = msg.additional_kwargs.get(TASK_PARTS_KEY, [])
                if existing:
                    tasks = tasks_reducer(existing, tasks)

                msg.additional_kwargs[TASK_PARTS_KEY] = tasks
                break

        return {"messages": messages}


def update_task_in_checkpoint(thread_id: str, task_id: str, status: str, extra: dict | None = None) -> bool:
    """Update a task's status directly in the Frappe checkpoint.

    Use this from outside the LangGraph agent (e.g. submit_file.py API endpoints)
    so that status changes like "Validating" and "Reviewing" are persisted to
    the same AIMessage that holds the original "Submitting" entry.

    It:
    1. Loads the checkpoint snapshot for the given thread.
    2. Finds the AIMessage whose additional_kwargs[TASK_PARTS_KEY] contains task_id.
    3. Merges the new status (and any extra payload) into that entry.
    4. Flushes the updated snapshot back to Frappe.

    Args:
        thread_id: LangGraph thread ID (= AI Thread docname).
        task_id:   The task docname to update (must already exist in the checkpoint).
        status:    New status string, e.g. "Validating", "Reviewing".
        extra:     Optional extra key/value pairs to merge into the task dict.

    Returns:
        True if the task was found and updated, False otherwise.
    """
    try:
        from langchain_core.messages import AIMessage, AIMessageChunk
        from langchain_core.runnables import RunnableConfig
        from gms.ai.agents_v2.checkpointer.frappe_in import FrappeBufferedCheckpointer

        config: RunnableConfig = {"configurable": {"thread_id": thread_id}}
        checkpointer = FrappeBufferedCheckpointer()
        checkpointer.load_from_frappe(config)

        # Get the latest checkpoint tuple from in-memory saver
        checkpoint_tuple = checkpointer.get_tuple(config)
        if not checkpoint_tuple:
            return False

        # Walk all channel values looking for messages
        channel_values = checkpoint_tuple.checkpoint.get("channel_values", {})
        messages = channel_values.get("messages", [])

        updated = False
        for msg in reversed(messages):
            if not isinstance(msg, (AIMessage, AIMessageChunk)):
                continue
            tasks = msg.additional_kwargs.get(TASK_PARTS_KEY, [])
            if not any(t.get("id") == task_id for t in tasks):
                continue  # This message doesn't own the task

            # Merge updated status into the matching task entry
            update_entry: Task = {"id": task_id, "status": status}
            if extra:
                update_entry.update(extra)  # type: ignore[arg-type]
            msg.additional_kwargs[TASK_PARTS_KEY] = tasks_reducer(tasks, [update_entry])
            updated = True
            break

        if updated:
            checkpointer.flush_to_frappe()

        return updated

    except Exception as exc:
        import logging
        logging.getLogger(__name__).warning(
            f"update_task_in_checkpoint failed for thread={thread_id} task={task_id}: {exc}"
        )
        return False
