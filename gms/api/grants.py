import frappe


@frappe.whitelist()
def get_grants_with_related(limit=50):
    # ----------------------------
    # STEP 1: Fetch Grants
    # ----------------------------
    grants = frappe.get_list(
        "Grant",
        fields=[
            "name",
            "title",
            "start_date",
            "end_date",
            "approved_amount",
            "lead_organization",
            "alias",
        ],
        limit=limit,
    )

    if not grants:
        return []

    grant_ids = [g["name"] for g in grants]

    # ----------------------------
    # STEP 2: Fetch Lead Organizations
    # ----------------------------
    org_ids = list(
        {g["lead_organization"] for g in grants if g.get("lead_organization")}
    )

    organizations = {}
    if org_ids:
        org_docs = frappe.get_list(
            "Grant Partner",
            fields=["name", "title"],
            filters={"name": ["in", org_ids]},
            limit_page_length=0,
        )
        organizations = {d["name"]: d for d in org_docs}

    # ----------------------------
    # STEP 3: Fetch Projects
    # ----------------------------
    projects = frappe.get_list(
        "Grant Project",
        fields=["name", "grant"],
        filters={"grant": ["in", grant_ids]},
        limit_page_length=0,
    )

    project_to_grant = {p["name"]: p["grant"] for p in projects}

    # Count projects per grant
    project_count = {}
    for p in projects:
        project_count[p["grant"]] = project_count.get(p["grant"], 0) + 1

    project_ids = [p["name"] for p in projects]

    # ----------------------------
    # STEP 4: Fetch Milestones
    # ----------------------------
    milestones = []
    milestone_ids = []

    if project_ids:
        milestones = frappe.get_list(
            "Grant Project Milestone",
            fields=["name", "project"],
            filters={"project": ["in", project_ids]},
            limit_page_length=0,
        )
        milestone_ids = [m["name"] for m in milestones]

    milestone_to_project = {m["name"]: m["project"] for m in milestones}

    # ----------------------------
    # STEP 5: Fetch Metric Values (Budget Spent)
    # ----------------------------
    budget_spent_per_grant = {}

    if milestone_ids:
        metric_rows = frappe.get_list(
            "Grant Metric Value",
            fields=["parent", "title", "data_string"],
            filters={"parent": ["in", milestone_ids]},
            limit_page_length=0,
        )
        # print("MATRIC ---> ", metric_rows)
        for row in metric_rows:
            if row.title != "Budget Spent":
                continue

            # Convert metric value safely
            try:
                print("TRY row.data_string ---> ", row.data_string)
                value = float(row.data_string or 0)
                print("TRY VALUE ---> ", value)
            except Exception:
                value = 0
            print("VALUE ---> ", value)
            milestone_id = row.parent
            project_id = milestone_to_project.get(milestone_id)
            grant_id = project_to_grant.get(project_id)

            if grant_id:
                budget_spent_per_grant[grant_id] = (
                    budget_spent_per_grant.get(grant_id, 0) + value
                )
    print("BUDGET SPENT PER GRANT ---> ", budget_spent_per_grant)
    # ----------------------------
    # STEP 6: Attach results to each Grant
    # ----------------------------
    for g in grants:
        grant_id = g["name"]

        g["organization"] = organizations.get(g.get("lead_organization"), {})
        g["total_projects"] = project_count.get(grant_id, 0)
        g["budget_spent"] = budget_spent_per_grant.get(grant_id, 0)

        # placeholders (same as your original)
        g["projects"] = []
        g["funding_agencies"] = []
        g["pi"] = []
        g["team_members"] = []

    return grants


@frappe.whitelist(allow_guest=True)
def clone_grant_project_milestone(source_id, project_id):
    """
    Clone a Grant Project Milestone including all child table rows,
    but assign it to the provided project_id.
    """

    if not source_id:
        frappe.throw("Source milestone ID is required")

    if not project_id:
        frappe.throw("Project ID is required")

    # Fetch source doc
    source = frappe.get_doc("Grant Project Milestone", source_id)
    source.check_permission("read")

    # Create new milestone
    new = frappe.new_doc("Grant Project Milestone")

    # ----- COPY MAIN FIELDS -----
    fields_to_copy = [
        # ❌ DO NOT COPY project
        "milestone_type",
        "submitted_at",
        "period_start",
        "period_end",
        "title",
        "metric_computed_at",
    ]

    for f in fields_to_copy:
        setattr(new, f, source.get(f))

    # ✅ OVERRIDE PROJECT
    new.project = project_id

    print("NEW DOC (before children) ---> ", new)

    # ----- COPY METRICS VALUES -----
    for row in source.metrics_values:
        new.append(
            "metrics_values",
            {
                "title": row.title,
                "type": row.type,
                "code": row.code,
                "data_string": row.data_string,
                "data_int": row.data_int,
                "data_float": row.data_float,
                "data_boolean": row.data_boolean,
            },
        )

    # ----- COPY ARTIFACTS -----
    for art in source.artifacts:
        new.append("artifacts", {"title": art.title, "link": art.link})

    # ----- COPY PARTNERS -----
    for p in source.partners:
        new.append(
            "partners",
            {
                "partner": p.partner,
                "contributions": p.contributions,
                "responsibility": p.responsibility,
            },
        )

    # ----- COPY CONTRIBUTORS -----
    for c in source.contributors:
        new.append("contributors", {"team_member": c.team_member, "role": c.role})

    # ----- SAVE -----
    new.insert()
    frappe.db.commit()

    return {
        "status": "success",
        "source_milestone": source_id,
        "project": project_id,
        "new_milestone": new.name,
    }
