"""Middleware for adding UI data state support to agents.

This middleware adds a `ui_data` field to the agent's state schema,
enabling tools to update UI data via Command returns. The data is
merged using a custom reducer to prevent overwriting.
"""

from typing import Annotated, Any

from langchain.agents import AgentState
from langchain.agents.middleware import AgentMiddleware
from langchain.agents.middleware.types import OmitFromInput

from gms.ai.agents_v2.utils.ui_stream_writer import ui_data_reducer


class UIDataState(AgentState):
    """State extension that includes ui_data field.

    The ui_data field is used to collect UI-related data from tools
    and persist it with messages. Uses a custom reducer to merge
    updates without overwriting.
    """

    ui_data: Annotated[dict[str, Any], ui_data_reducer, OmitFromInput]


class UIDataMiddleware(AgentMiddleware[UIDataState, Any]):
    """Middleware that adds ui_data field to agent state schema.

    This middleware enables tools to update ui_data via Command returns.
    The ui_data is merged using ui_data_reducer to support multiple updates.

    Add this middleware to both:
    1. The SubAgent that contains tools needing ui_data
    2. The main agent to receive ui_data from SubAgents

    Usage:
        # In SubAgent
        research_agent = SubAgent(
            ...
            middleware=[
                UIDataMiddleware(),  # Enable ui_data for tools in this agent
                KBSearchMiddleware(...),
            ],
        )

        # In main agent
        create_deep_agent(
            ...
            middleware=[UIDataMiddleware()],  # Receive ui_data from SubAgents
        )

    Tools can then return:
        return Command(
            update={
                "messages": [ToolMessage(...)],
                "ui_data": writer.get_state_update(),
            }
        )

    The ui_data will flow:
    Tool → SubAgent state → Main agent state (via _return_command_with_state_update)
    """

    state_schema = UIDataState
    tools = []  # No additional tools
