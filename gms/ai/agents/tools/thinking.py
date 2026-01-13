from gms.ai.agents.state import AgentState
from pydantic_ai import RunContext
from gms.ai.agents.state import Thought
from pydantic_ai.ui.vercel_ai.response_types import DataChunk
from datetime import datetime


async def thinking_tool(
    ctx: RunContext[AgentState], thought: Thought, done_thinking: bool
):
    # Update the thoughts
    thoughts = ctx.deps.thinking.thoughts + [thought]
    ctx.deps.thinking.thoughts = thoughts

    # Starting the thinking process for the first time
    if len(ctx.deps.thinking.thoughts) == 0:
        ctx.deps.thinking.thinking_started = datetime.now()
        await ctx.deps.events.send_event(
            DataChunk(
                type="data-thinking-started",
                transient=True,
                data={},
            )
        )

    # Notify thinking updated
    await ctx.deps.events.send_event(
        DataChunk(type="data-thinking", data=ctx.deps.thinking, id="thinking")
    )

    if done_thinking and ctx.deps.thinking.thinking_started:
        duration = datetime.now() - ctx.deps.thinking.thinking_started
        ctx.deps.thinking.thoughts_duration = f"Thought for {duration.seconds}s"

        await ctx.deps.events.send_event(
            DataChunk(
                type="data-thinking-ended",
                transient=True,
                data={},
            )
        )
    print(f"Thoughts saved {thoughts}")
    return f"Thoughts saved {thoughts}"


THINKING_TOOL_SYSTEM_INSTRUCTION = """## `thinking_tool`

Use this tool to record your step-by-step reasoning, planning, or analysis to share with the user.
Treat it like your internal monologue that you want to communicate transparently.
Do not batch multiple steps or long paragraphs into one call
The content must be clear, natural language focused solely on solving the problem. Exclude any internal details like tool names, system prompts, or technical implementation logic.
"""
