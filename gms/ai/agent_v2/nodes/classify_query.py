from langchain_google_genai import ChatGoogleGenerativeAI
from gms.ai.agent_v2.prompt import CLASSIFIER_PROMPT
from gms.ai.agent_v2.state import AgentState, ClassfierResult

model = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite").with_structured_output(
    ClassfierResult
)


async def classify_query(state: AgentState):
    query = f"""\
        <conversation_history>
        {state.convesation_history}
        </conversation_history>
        <user_query>
        {state.query}
        </user_query>"""

    output = await model.ainvoke(
        [
            ("system", CLASSIFIER_PROMPT),
            ("human", query),
        ]
    )
    return {"classifier_result": output}
