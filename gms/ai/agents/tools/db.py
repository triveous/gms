import frappe
from pydantic_ai import RunContext

from gms.ai.agents.state import AgentState


def data_overview(ctx: RunContext[AgentState]):
    results = {}
    results["grants"] = frappe.get_list(
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
    results["projects"] = frappe.get_list(
        "Grant Project",
        fields=["name", "grant", "title", "alias", "start_date", "end_date"],
    )

    results["milestone_updates"] = frappe.get_list(
        "Grant Project Milestone",
        fields=[
            "name",
            "title",
            "project",
            "milestone_type",
            "submitted_at",
            "period_start",
            "period_end",
        ],
    )

    print(f"Data Overview {results}")
    return frappe.as_json(results)


DATA_OVERVIEW_SYSTEM_INSTRUCTION = """## `data_overview`

You have access to the `data_overview` tool to help to great a broader picture of all the grant and project that user has access to.
You should never use the tool to get the entire information about the grant and project. You should look for more information in some other place

You should use this tool to know if user is asking query from any of these grant/project
name should always be treated as id. 
Example - if the grant has name field: that is the id of the grant in the system, same as any other information
"""
