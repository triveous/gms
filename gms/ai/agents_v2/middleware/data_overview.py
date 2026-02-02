"""DataOverview middleware for loading system data context.

This middleware loads an overview of grants, projects, and milestones
from the database and appends it to the system prompt via wrap_model_call.

The data is loaded once in before_agent and stored in state, then used
in wrap_model_call to append to the system message.
"""

import json
from typing import Any

import frappe
from langchain.agents.middleware import AgentMiddleware, AgentState
from langchain_core.tools import StructuredTool

DATA_OVERVIEW_PROMPT_TEMPLATE = """## Data Overview in the Grant Management System

The following is an overview of the current data in the system:

{data_overview}
"""

DATA_OVERVIEW_TOOL_DESCRIPTION = """Get an overview of the data in the Grant Management System.

Returns a structured overview of all grants, projects, and milestones that the user has access to.
Use this tool to understand what grants, projects, and milestones exist in the system.
"""


def get_data_overview() -> dict:
    """Load overview of grants, projects, and milestones.

    frappe.get_list automatically filters based on user permissions.

    Returns:
        Dict containing grants with their projects and milestones.
    """
    try:
        grants = frappe.get_list(
            "Grant",
            fields=[
                "name",
                "title",
                "alias",
                "start_date",
                "end_date",
                "description",
                "approval_identifier",
                "approved_amount",
            ],
        )

        projects = frappe.get_list(
            "Grant Project",
            fields=["name", "grant", "title", "alias", "start_date", "end_date"],
        )

        milestones = frappe.get_list(
            "Grant Project Milestone",
            fields=[
                "title",
                "project",
                "milestone_type",
                "submitted_at",
                "period_start",
                "period_end",
            ],
        )

        # Nest milestones under projects
        for p in projects:
            milestone_list = []
            for m in milestones:
                if m.get("project") == p.get("name"):
                    milestone_list.append(m)
            p["milestones"] = milestone_list

        # Nest projects under grants
        for g in grants:
            grant_projects = []
            for p in projects:
                if p.get("grant") == g.get("name"):
                    project_copy = {k: v for k, v in p.items() if k != "grant"}
                    grant_projects.append(project_copy)
            g["projects"] = grant_projects

        print(f"Grant {grants}")
        return {"grants": grants}

    except Exception as e:
        import traceback

        traceback.print_exception(e)
        print(f"Failed to load data overview: {e}")
        return {"grants": [], "error": "Failed to load data overview"}


def _data_overview_tool() -> str:
    print("Getting data overview")
    """Tool function that returns data overview as JSON string."""
    overview = get_data_overview()
    return json.dumps(overview, indent=2, default=str)


def create_data_overview_tool() -> StructuredTool:
    """Create the data_overview tool.

    Returns:
        StructuredTool that returns data overview information.
    """
    return StructuredTool.from_function(
        func=_data_overview_tool,
        name="data_overview",
        description=DATA_OVERVIEW_TOOL_DESCRIPTION,
    )


class DataOverviewState(AgentState):
    """State with data overview field."""

    data_overview: dict[str, Any]


class DataOverviewMiddleware(AgentMiddleware[DataOverviewState, Any]):
    """Middleware that loads data overview and appends it to the system prompt.

    This middleware:
    1. Loads data overview once in before_agent and stores in state
    2. Uses wrap_model_call to append the data overview to the system message
    3. Provides a data_overview tool to fetch the overview on demand

    Usage:
        agent = create_deep_agent(
            ...
            middleware=[DataOverviewMiddleware()],
        )
    """

    def __init__(self):
        """Initialize the middleware with the data_overview tool."""
        self.data_overview_tool = create_data_overview_tool()
        self.tools = [self.data_overview_tool]
