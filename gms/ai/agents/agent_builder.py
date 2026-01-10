from dataclasses import dataclass
from typing import Any

import frappe
from langchain_core.documents.base import Document
from pydantic_ai import Agent, RunContext, Tool, ToolReturn

from gms.ai.doctype.ai_agent.ai_agent import AIAgent as AIAgentConf
from gms.ai.doctype.ai_subagent.ai_subagent import AISubAgent as AISubAgentConf


@dataclass
class SupportDependencies:
    search_grant: str = None
    search_project: str = None
    search_project_milestone: str = None


def read_knowledge_base(ctx: RunContext[SupportDependencies], query: str):
    """
    Reads the knowledgebase to find out answer query
    :type query: str
    :returns Document talking about the query including the source
    """
    from gms.ai.kb.knowledge_base import KnowledgeBase

    kb = KnowledgeBase()

    print(f"Performing search {query}")
    print("=" * 50)
    print("\n")

    expr_part = []
    expr = None
    if ctx.deps.search_grant:
        expr_part.append(f'grant_id == "{ctx.deps.search_grant}"')

    if ctx.deps.search_project:
        expr_part.append(f'project_id == "{ctx.deps.search_project}"')

    if ctx.deps.search_project_milestone:
        expr_part.append(
            f'project_milestone_id == "{ctx.deps.search_project_milestone}"'
        )

    if len(expr_part) > 0:
        expr = " or ".join(expr_part)

    documents = kb.retrieve_raw(query, expr=expr)

    if len(documents) == 0:
        return "No result for the query"

    def document_content(doc: Document):
        raw_text = doc.metadata.get("raw_text")
        summary = doc.metadata.get("summary")
        if raw_text and summary:
            doc.metadata.pop("raw_text")
            doc.metadata.pop("summary")
            return f"""\
            <document>
                <content>{raw_text}</content>
                <meta>{doc.metadata}</meta>
            </document>
            """

        return f"""\
            <document>
                <content>{doc.page_content}</content>
                <meta>{doc.metadata}</meta>
            </document>
            """

    content = []
    has_none_text = False
    for doc in documents:
        content.append(document_content(doc))
        # if doc.metadata.get("images") is None:
        #     continue
        # images = json.loads(doc.metadata["images"])
        # for img in images:
        #     try:
        #         if img["uri"] is not None:
        #             mime_type = img["mime_type"]
        #             uri = img["uri"]
        #             image = PILImage.open(img["uri"])
        #             buffer = BytesIO()
        #             image.save(buffer, format=mime_type.split("/")[1])
        #             content.append(
        #                 BinaryImage(
        #                     data=buffer.getvalue(),
        #                     media_type=mime_type,
        #                     identifier=uri,
        #                 )
        #             )
        #     except Exception:
        #         pass

    final_content = None
    if has_none_text:
        final_content = ToolReturn(return_value="Document fetched", content=content)
    else:
        final_content = "\n".join(content)

    print(final_content)
    return final_content


def reflect():
    return "Do you have enough information to proceed?"


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
    tools = [
        prepare_sub_agent_tool(sub_agent_conf) for sub_agent_conf in conf.sub_agents
    ]

    if conf.enable_knowledgebase_tool:
        tools.append(Tool(read_knowledge_base, takes_ctx=True))

    if conf.enable_reflect_tool:
        tools.append(Tool(reflect))

    return tools


# Trigger a sub-agent as a tool call
def prepare_sub_agent_tool(sub_agent_conf: AISubAgentConf) -> Tool:
    agent = build_agent(sub_agent_conf.agent)

    description = f"""{sub_agent_conf.tool_description}
    Args:
        query: str Query to process by the sub-agent
    """

    async def trigger_sub_agent(ctx: RunContext[SupportDependencies], query: str):
        result = await agent.run(query, deps=ctx.deps)
        return result.output

    return Tool(
        trigger_sub_agent,
        name=sub_agent_conf.tool_name,
        description=description,
        takes_ctx=True,
    )


# Prepare an agent and its tools as well all the sub-agents recursively
def build_agent(id: str):
    agent_conf: AIAgentConf = frappe.get_doc("AI Agent", id)

    agent = Agent(
        model=agent_conf.model,
        deps_type=SupportDependencies,
        model_settings=agent_conf.model_setting_dict,
        instructions=agent_conf.instruction,
        tools=prepare_tools(agent_conf),
    )
    merge_instruction(agent=agent, conf=agent_conf)

    return agent
