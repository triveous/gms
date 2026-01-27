from pydantic_ai import RunContext
from gms.ai.agents_v2.state import AgentContext


def create_goal(ctx: RunContext[AgentContext], goal: str):
    print(f"Goal triggered {goal}")
    ctx.deps.state.plan().add_goal(goal)
    ctx.deps.notify_block_changes()
