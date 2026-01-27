# from frappe import Document
# from pydantic_ai import Agent, Tool, RunContext
# from httpx import AsyncClient
# from pydantic_ai.models.google import GoogleModel
# from pydantic_ai.providers.google import GoogleProvider
# from gms.ai.agent_v2.state import AgentContext
# from gms.ai.agents.tools.kb import read_knowledge_base


# def goal_tool(ctx: RunContext[AgentContext], goal: str):
#     ctx.deps.add_goal(goal)
#     return


# # Prepare an agent and its tools as well all the sub-agents recursively
# def build_agent2(agent_conf: Document):
#     agent = Agent(
#         model=GoogleModel(
#             agent_conf.model.split(":")[1],
#             provider=GoogleProvider(http_client=AsyncClient()),
#         ),
#         deps_type=AgentContext,
#         model_settings=agent_conf.model_setting_dict,
#         instructions="",
#         tools=[],
#         tool_timeout=300,
#         retries=5,
#     )
#     return agent
