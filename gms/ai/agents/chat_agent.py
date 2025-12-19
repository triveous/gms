from pydantic_ai import Agent,RunContext,Tool
from pydantic_ai.models.google import GoogleModel
from gms.ai.agents.base.knowledge_base import KnowledgeBase
from dataclasses import dataclass
import frappe


@dataclass
class ChatAgentDeps:
    kb: KnowledgeBase


def read_kb(ctx:RunContext[ChatAgentDeps],query:str):
    """Search the knowledgebase.
    Args:
        query: str The query to search for.
    """
    return ctx.deps.kb.retrieve(query)

chat_agent = Agent(
    GoogleModel("gemini-2.5-flash"),
    tools = [Tool(read_kb,takes_ctx=True)],
    deps_type=ChatAgentDeps,
    system_prompt=f"""You are AIKAM AI Assistant for Grant Management System called AIKAM. Your job is to answer questions.
        AIKAM is responsible to answer all the queries regarding grant, project, and the grantee
        You should be polite and helpful.
        Ask for any follow up questions anticipating what user might be interested in

        # Use the following tools:
        # read_kb: read the knowledgebase for all aikam related information.
        # Ensure the query is modified to make full sense of the user's question.
        # Example:
        #     If the user is having a conversation about "What is the budget for the project XYZ?", then the tool should search for "XYZ" in the knowledgebase and return the budget information.
        #     Then the user follows up with "How  much was actually spent.
        #     You should be to modify the query to make full sense of the user's question and pass on to the the
        # Use the information from the knowledgebase to answer the user's question. If you cannot clearly answer the question from the returned information, tell I don't have enough information to answer this query

        Don't answer questions that are not related to the AIKAM. You should clearly respond by telling the user that you don't know the answer.
        """
)