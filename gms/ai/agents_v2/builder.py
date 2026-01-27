from httpx import AsyncClient
from pydantic_ai import Agent, Tool
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider

from gms.ai.agents_v2.state import AgentContext
from gms.ai.agents_v2.tools.goal import create_goal


# Prepare an agent and its tools as well all the sub-agents recursively
def build_agent(agent_conf):
    agent = Agent(
        model=GoogleModel(
            agent_conf.model.split(":")[1],
            provider=GoogleProvider(http_client=AsyncClient()),
        ),
        deps_type=AgentContext,
        model_settings=agent_conf.model_setting_dict,
        instructions="You are helful assistant. Your role is answer all the user query but before that should use the create_goal to define what you will do",
        tools=[
            Tool(
                create_goal,
                description="Define the goal of the next work that you will do. Keep it short and crisp so that user can understand. Avoid anything technical and mention of any tools. User won't be able to understand anything about the tool",
                takes_ctx=True,
            )
        ],
        tool_timeout=300,
        retries=5,
        event_stream_handler=lambda ctx, ev: print(ev),
    )
    return agent
