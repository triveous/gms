import frappe


def data_overview():
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

    for p in projects:
        milestone_projects = []
        for m in milestones:
            if m["project"] == p["name"]:
                milestone_projects.append(m)
                del m["project"]

        # Delete the name of project as it is not more needed
        del p["name"]
        p["milestones"] = milestone_projects

    for g in grants:
        grant_projects = []
        for p in projects:
            if p["grant"] == g["name"]:
                grant_projects.append(p)
                # Delete the ref
                del p["grant"]

        # Delete the name of grant as it is not more needed
        del g["name"]
        g["projects"] = grant_projects

    return frappe.as_json({"grants": grants})


DATA_OVERVIEW_SYSTEM_INSTRUCTION = """## `data_overview`

You have access to the `data_overview` tool to help to great a broader picture of all the grant and project that user has access to.
You should never use the tool to get the entire information about the grant and project. You should look for more information in some other place

You should use this tool to know if user is asking query from any of these grant/project
name should always be treated as id. 
Example - if the grant has name field: that is the id of the grant in the system, same as any other information
"""
