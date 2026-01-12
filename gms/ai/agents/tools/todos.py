from pydantic_ai import RunContext
from pydantic_ai.ui.vercel_ai.response_types import DataChunk

from gms.ai.agents.state import AgentState, Todo

TODO_SYSTEM_INSTRUCTION = """## `write_todos`

You have access to the `write_todos` tool to help you manage and plan complex objectives.
Use this tool for complex objectives to ensure that you are tracking each necessary step and giving the user visibility into your progress.
This tool is very helpful for planning complex objectives, and for breaking down these larger complex objectives into smaller steps.

It is critical that you mark todos as completed as soon as you are done with a step. Do not batch up multiple steps before marking them as completed.
For simple objectives that only require a few steps, it is better to just complete the objective directly and NOT use this tool.
Writing todos takes time and tokens, use it when it is helpful for managing complex many-step problems! But not for simple few-step requests.

## Important To-Do List Usage Notes to Remember
- The `write_todos` tool should never be called multiple times in parallel.
- Don't be afraid to revise the To-Do list as you go. New information may reveal new tasks that need to be done, or old tasks that are irrelevant."""


async def write_todos(ctx: RunContext[AgentState], todos: list[Todo]):
    """
    Use this tool to create and manage a structured task list for your current work session. This helps you track progress, organize complex tasks, and demonstrate thoroughness to the user.
    """
    ctx.deps.planning.todos = todos
    await ctx.deps.events.send_event(
        DataChunk(type="data-todos", id="planning", data={"todos": todos})
    )

    in_progress_todo = [t for t in todos if t.status == "in_progress"]
    if (len(in_progress_todo)) > 0:
        last_todo = in_progress_todo[-1]
        await ctx.deps.events.send_event(
            DataChunk(
                type="data-tool-in-progress", transient=True, data={"todo": last_todo}
            )
        )

    print(f"Updates the todos {todos}")
    return f"Todos Updated {todos}"
