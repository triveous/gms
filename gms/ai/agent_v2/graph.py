from langgraph.constants import END, START
from langgraph.graph import StateGraph
from gms.ai.agent_v2.nodes.classify_query import classify_query
from gms.ai.agent_v2.state import (
    AgentContext,
    AgentState,
    StepBlock,
    IntialQueryStep,
)
from gms.ai.agents.ui import stream_async_iterator
from gms.ai.kb.knowledge_base import KnowledgeBase

async def set_initial_query(state: AgentState):
    step_block = StepBlock(
        step_content=StepBlock.Content(
            steps=[
                IntialQueryStep(
                    type="INTIAL_QUERY",
                    initial_query=IntialQueryStep.Content(query=state.query),
                )
            ]
        )
    )
    blocks = state.blocks
    blocks.append(step_block)
    return {"blocks": blocks}


async def route_query_to_task(tate: AgentState):
    pass


graph = StateGraph(AgentState, AgentContext)
graph.add_node(set_initial_query)
graph.add_node(classify_query)
graph.add_edge(START, "set_initial_query")
graph.add_edge("set_initial_query", "classify_query")
graph.add_edge("classify_query", END)

app = graph.compile()


def q(query: str):
    for e in stream_async_iterator(q_async(query)):
        print(f"{'=' * 50}\n")
        print(f"Event: {e}\n{'=' * 50}\n\n")
        yield f"data: {e}\n\n"


async def q_async(query: str):
    state = AgentState(query=query)
    context: AgentContext = {"kb": KnowledgeBase()}

    async for values in app.astream(state, context=context, stream_mode=["values"]):
        yield values
