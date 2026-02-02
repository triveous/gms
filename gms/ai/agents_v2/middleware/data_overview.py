"""DataOverview middleware for loading system data context.

This middleware loads an overview of grants, projects, and milestones
from the database and appends it to the system prompt via wrap_model_call.

The data is loaded once in before_agent and stored in state, then used
in wrap_model_call to append to the system message.
"""

from typing import Any, Callable

import frappe
from deepagents.middleware._utils import append_to_system_message
from langchain.agents.middleware import AgentMiddleware
from langchain.agents.middleware.types import ModelRequest, ModelResponse
from typing_extensions import TypedDict


DATA_OVERVIEW_PROMPT_TEMPLATE = """## Data Overview in the Grant Management System

The following is an overview of the current data in the system:

{data_overview}
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


class DataOverviewState(TypedDict, total=False):
    """State with data overview field."""

    data_overview: dict | None


class DataOverviewMiddleware(AgentMiddleware[DataOverviewState, Any]):
    """Middleware that loads data overview and appends it to the system prompt.

    This middleware:
    1. Loads data overview once in before_agent and stores in state
    2. Uses wrap_model_call to append the data overview to the system message

    Usage:
        agent = create_deep_agent(
            ...
            middleware=[DataOverviewMiddleware()],
        )
    """

    state_schema = DataOverviewState

    def before_agent(
        self, state: DataOverviewState, runtime: Any
    ) -> dict[str, Any] | None:
        """Load data overview and store in state.

        Args:
            state: Current agent state
            runtime: Agent runtime context

        Returns:
            State update with data_overview field
        """

        if state.get("data_overview") is not None:
            return

        data_overview = get_data_overview()
        return {"data_overview": data_overview}

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        """Append data overview from state to the system prompt.

        Args:
            request: The model request being processed.
            handler: The handler function to call with the modified request.

        Returns:
            The model response from the handler.
        """
        # Get data overview from state (loaded in before_agent)
        data_overview = request.state.get("data_overview", {})

        if data_overview:
            # Convert dict to JSON string for the prompt
            data_overview_json = frappe.as_json(data_overview, indent=2)

            # Format the system prompt addition
            data_overview_prompt = DATA_OVERVIEW_PROMPT_TEMPLATE.format(
                data_overview=data_overview_json
            )

            # Append to system message
            new_system_message = append_to_system_message(
                request.system_message, data_overview_prompt
            )
            request = request.override(system_message=new_system_message)

        return handler(request)
