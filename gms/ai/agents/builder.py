import frappe
from gms.ai.agents.tools.kb import read_knowledge_base
from langchain_core.documents.base import Document
from pydantic_ai import Agent, RunContext, Tool

from gms.ai.agents.state import AgentState
from gms.ai.agents.tools.todos import TODO_SYSTEM_INSTRUCTION, write_todos
from gms.ai.doctype.ai_agent.ai_agent import AIAgent as AIAgentConf
from gms.ai.doctype.ai_subagent.ai_subagent import AISubAgent as AISubAgentConf

BASE_PROMPT = "In order to complete the objective that the user asks of you, you have access to a number of standard tools."


# Prepare dynamic instructions as per the configuration
def merge_instruction(agent: Agent, conf: AIAgentConf):
    if conf.add_user_name_instruction:

        @agent.instructions
        def append_user_name():
            if frappe.session.user_fullname:
                return f"User full name is {frappe.session.user_fullname}"
            return ""

    if conf.add_current_time_instruction:

        @agent.instructions
        def todays_date():
            from datetime import datetime

            now = datetime.now().strftime("%I:%M%p on %B %d, %Y")
            return f"Current time is {now}"


# Configure agent tools
def prepare_tools(conf: AIAgentConf):
    tools = []

    if conf.enable_todo_tools:
        tools.append(Tool(write_todos, takes_ctx=True))

    if conf.enable_knowledgebase_tool:
        tools.append(Tool(read_knowledge_base, takes_ctx=True))

    tools = [
        *tools,
        *[prepare_sub_agent_tool(sub_agent_conf) for sub_agent_conf in conf.sub_agents],
    ]
    return tools


# Trigger a sub-agent as a tool call
def prepare_sub_agent_tool(sub_agent_conf: AISubAgentConf) -> Tool:
    agent = build_agent(sub_agent_conf.agent)

    description = f"""{sub_agent_conf.tool_description}
    Args:
        query: str Query to process by the sub-agent
    """

    async def trigger_sub_agent(ctx: RunContext[AgentState], query: str):
        result = await agent.run(query, deps=ctx.deps)
        return result.output

    return Tool(
        trigger_sub_agent,
        name=sub_agent_conf.tool_name,
        description=description,
        takes_ctx=True,
    )


# Prepare an agent and its tools as well all the sub-agents recursively
def build_agent(agent_conf: Document):
    agent = Agent(
        model=agent_conf.model,
        deps_type=AgentState,
        model_settings=agent_conf.model_setting_dict,
        instructions=agent_conf.instruction + "\n\n" + BASE_PROMPT
        if agent_conf.instruction
        else BASE_PROMPT,
        tools=prepare_tools(agent_conf),
    )

    @agent.instructions
    def tool_usage_instruction():
        instructions = []
        if agent_conf.enable_todo_tools:
            instructions.append(TODO_SYSTEM_INSTRUCTION)
        
        instructions = "\n".join(instructions)
        return f"# TOOL Usage \n{instructions}"

    merge_instruction(agent=agent, conf=agent_conf)

    return agent
