from datetime import date, datetime

import frappe


def safe_parse_date(ps):
    """Return a datetime.date object or None for a variety of inputs."""
    if not ps:
        return None

    # already datetime/date
    if isinstance(ps, datetime):
        return ps.date()
    if isinstance(ps, date):
        return ps

    # string -> normalize
    if isinstance(ps, str):
        s = ps.strip()
        if s == "":
            return None
        # if time portion present, drop it
        if " " in s:
            s = s.split(" ")[0]
        # try common formats
        for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d", "%d/%m/%Y"):
            try:
                return datetime.strptime(s, fmt).date()
            except Exception:
                pass
    return None


def fy_start_and_quarter_end(qval):
    """
    Returns (fy_start_date, quarter_end_date)
    for Qx-YYYY-YYYY
    """
    if not qval.startswith("Q"):
        frappe.throw("Quarter value must be like Q3-2024-2025")

    parts = qval.split("-")
    q = parts[0]
    fy_start_year = int(parts[1])
    fy_end_year = int(parts[2])

    fy_start = date(fy_start_year, 4, 1)

    if q == "Q1":
        q_end = date(fy_start_year, 6, 30)
    elif q == "Q2":
        q_end = date(fy_start_year, 9, 30)
    elif q == "Q3":
        q_end = date(fy_start_year, 12, 31)
    elif q == "Q4":
        q_end = date(fy_end_year, 3, 31)
    else:
        frappe.throw("Invalid quarter")

    return fy_start, q_end


@frappe.whitelist()
def get_grant_projects_by_quarter(grant_id, quarter_value):
    print(
        "get_grant_projects_by_quarter called with grant_id:",
        grant_id,
        "and quarter_value:",
        quarter_value,
    )
    """
    Fetch all projects for a grant that have milestones falling in a specific quarter.

    quarter_value: e.g., "Q2-2025-2026" or "2025-2026" (for yearly)
    """
    if not grant_id or not quarter_value:
        frappe.throw("Grant ID and quarter_value are required")
    print("Fetching projects for Grant:", grant_id, "Quarter/Year:", quarter_value)
    # ----------------------------
    # STEP 1: Fetch Projects
    # ----------------------------
    projects = frappe.get_list(
        "Grant Project",
        fields=[
            "name",
            "title",
            "alias",
            "start_date",
            "end_date",
            "lead_organization",
        ],
        filters={"grant": grant_id},
        limit_page_length=0,
    )
    project_ids = [p["name"] for p in projects]
    if not project_ids:
        return {"projects": [], "total_budget_spent": 0, "total_projects": 0}
    print("Found Projects ------------------:", project_ids)
    # ----------------------------
    # STEP 1 a: Fetch Projects Lead Organizations
    # ----------------------------
    partner_ids = [p["lead_organization"] for p in projects if p["lead_organization"]]
    partners = frappe.get_list(
        "Grant Partner",
        filters={"name": ["in", partner_ids]},
        fields=["name", "title"],
        limit_page_length=0,
    )
    partner_map = {p["name"]: p["title"] for p in partners}
    for project in projects:
        project["lead_organization"] = partner_map.get(
            project.get("lead_organization"), {}
        )
    # ----------------------------
    # STEP 2: Fetch Milestones
    # ----------------------------
    milestones = frappe.get_list(
        "Grant Project Milestone",
        fields=[
            "name",
            "project",
            "title",
            "period_start",
            "creation",
            "forecasted_amount",
        ],
        filters={"project": ["in", project_ids]},
        order_by="creation desc",
        limit_page_length=0,
    )
    print("Found Milestones ------------------:", [m["name"] for m in milestones])

    # Helper: Calculate quarter start/end dates for a FY
    def quarter_start_end(quarter, fy_start_year):
        """
        quarter: Q1/Q2/Q3/Q4
        fy_start_year: starting year of FY (Apr 1)
        """
        fy_end_year = fy_start_year + 1
        if quarter == "Q1":
            return date(fy_start_year, 4, 1), date(fy_start_year, 6, 30)
        elif quarter == "Q2":
            return date(fy_start_year, 7, 1), date(fy_start_year, 9, 30)
        elif quarter == "Q3":
            return date(fy_start_year, 10, 1), date(fy_start_year, 12, 31)
        elif quarter == "Q4":
            return date(fy_end_year, 1, 1), date(fy_end_year, 3, 31)
        else:
            return None, None

    # Determine if it's yearly or quarterly
    filtered_milestone_ids = []
    if quarter_value.startswith("Q"):
        # Quarterly filter
        try:
            q, fy_str = (
                quarter_value.split("-")[0],
                quarter_value.split("-")[1] + "-" + quarter_value.split("-")[2],
            )
            fy_start_year = int(fy_str.split("-")[0])
            start_date, end_date = quarter_start_end(q, fy_start_year)
        except Exception:
            frappe.throw("Invalid quarter_value format")

        # Filter milestones
        for m in milestones:
            ps = m.get("period_start")
            if not ps:
                continue
            try:
                ps_date = safe_parse_date(ps)
            except Exception:
                continue
            if start_date <= ps_date <= end_date:
                filtered_milestone_ids.append(m["name"])
    else:
        # Yearly filter
        fy_start_year = int(quarter_value.split("-")[0])
        fy_end_year = int(quarter_value.split("-")[1])
        start_date = date(fy_start_year, 4, 1)
        end_date = date(fy_end_year, 3, 31)
        for m in milestones:
            ps = m.get("period_start")
            if not ps:
                continue
            try:
                ps_date = datetime.strptime(ps, "%Y-%m-%d").date()
            except Exception:
                continue
            if start_date <= ps_date <= end_date:
                filtered_milestone_ids.append(m["name"])

    # ----------------------------
    # STEP 3: Filter milestones and projects
    # ----------------------------
    milestone_map = {
        m["name"]: m for m in milestones if m["name"] in filtered_milestone_ids
    }
    project_to_milestones = {}
    for _, m in milestone_map.items():
        pid = m["project"]
        project_to_milestones.setdefault(pid, []).append(m)

    milestone_ids = list(milestone_map.keys())

    # ----------------------------
    # STEP 4: Fetch ALL Metric Values
    # ----------------------------
    milestone_metrics = {}
    budget_spent_per_milestone = {}
    total_budget_spent = 0

    if milestone_ids:
        metric_rows = frappe.get_all(
            "Grant Metric Value",
            fields=[
                "parent",
                "title",
                "type",
                "data_string",
                "data_int",
                "data_float",
                "data_boolean",
            ],
            filters={"parent": ["in", milestone_ids]},
            limit_page_length=0,
        )
    else:
        metric_rows = []

    for row in metric_rows:
        mid = row["parent"]
        title = row["title"]
        mtype = (row.get("type") or "").lower()

        if mtype == "int":
            value = row.get("data_int")
        elif mtype == "float":
            value = row.get("data_float")
        elif mtype == "boolean":
            value = row.get("data_boolean")
        else:
            value = row.get("data_string")

        milestone_metrics.setdefault(mid, {})[title] = value

        if title == "Budget Spent":
            try:
                numeric_value = float(value) if value is not None else 0
            except Exception:
                numeric_value = 0
            budget_spent_per_milestone[mid] = (
                budget_spent_per_milestone.get(mid, 0) + numeric_value
            )
            total_budget_spent += numeric_value

    # ----------------------------
    # STEP 5: Fetch Partners & Contributors
    # ----------------------------

    partners_map = {}
    contributors_map = {}

    if milestone_ids:
        # Fetch Partners
        partner_rows = frappe.get_list(
            "Grant Project Milestone Partner",
            fields=["parent", "partner", "responsibility"],
            filters={
                "parent": ["in", milestone_ids],
                "parenttype": "Grant Project Milestone",
                "parentfield": "partners",
            },
            limit_page_length=0,
        )

        # Fetch Contributors
        contributor_rows = frappe.get_list(
            "Grant Project Milestone Contributor",
            fields=["parent", "team_member", "role"],
            filters={
                "parent": ["in", milestone_ids],
                "parenttype": "Grant Project Milestone",
                "parentfield": "contributors",
            },
            limit_page_length=0,
        )
        partner_ids = set()
        member_ids = set()

        for p in partner_rows:
            if p.get("partner"):
                partner_ids.add(p["partner"])

        for c in contributor_rows:
            if c.get("team_member"):
                member_ids.add(c["team_member"])

        partner_title_map = {}
        member_title_map = {}

        # Fetch Grant Partner titles
        if partner_ids:
            partners = frappe.get_list(
                "Grant Partner",
                fields=["name", "title"],
                filters={"name": ["in", list(partner_ids)]},
                limit_page_length=0,
            )
            partner_title_map = {p["name"]: p["title"] for p in partners}

        # Fetch Grant Member titles
        if member_ids:
            members = frappe.get_list(
                "Grant Member",
                fields=["name", "name1 as title"],
                filters={"name": ["in", list(member_ids)]},
                limit_page_length=0,
            )
            member_title_map = {m["name"]: m["title"] for m in members}

        # Group by milestone
        for p in partner_rows:
            mid = p["parent"]
            pid = p.get("partner")

            partners_map.setdefault(mid, []).append(
                {
                    "id": pid,
                    "title": partner_title_map.get(pid),
                    "responsibility": p.get("responsibility"),
                }
            )

        for c in contributor_rows:
            mid = c["parent"]
            mid_id = c.get("team_member")

            contributors_map.setdefault(mid, []).append(
                {
                    "id": mid_id,
                    "title": member_title_map.get(mid_id),
                    "role": c.get("role"),
                }
            )

    # ----------------------------
    # STEP 6: Build Final Project Objects
    # ----------------------------
    full_projects = []
    for p in projects:
        pid = p["name"]
        if pid not in project_to_milestones:
            continue  # skip projects with no milestones in this quarter

        proj_obj = {**p, "milestones": []}

        for m in project_to_milestones.get(pid, []):
            mid = m["name"]
            partners = partners_map.get(mid, [])
            contributors = contributors_map.get(mid, [])

            # Combine partners & contributors into one array
            partners_and_contributors = []

            max_len = max(len(partners), len(contributors))

            for i in range(max_len):
                partners_and_contributors.append(
                    {
                        "partner": partners[i] if i < len(partners) else None,
                        "contributor": contributors[i]
                        if i < len(contributors)
                        else None,
                    }
                )

            proj_obj["milestones"].append(
                {
                    "name": mid,
                    "milestone_title": m.get("title"),
                    "period_start": m.get("period_start"),
                    "last_updated": m.get("creation"),
                    "forecasted_amount": m.get("forecasted_amount"),
                    "metrics": milestone_metrics.get(mid, {}),
                    "partners_and_team_members": partners_and_contributors,
                }
            )

        full_projects.append(proj_obj)

    # ----------------------------
    # STEP 7: Calculate Overall Utilization (FY-to-date)
    # ----------------------------

    fy_start, q_end = fy_start_and_quarter_end(quarter_value)

    overall_forecasted = 0
    overall_spent = 0

    # 1️⃣ Sum forecasted amounts till quarter
    for m in milestones:
        ps = safe_parse_date(m.get("period_start"))
        if not ps:
            continue

        if fy_start <= ps <= q_end:
            overall_forecasted += float(m.get("forecasted_amount") or 0)

    # 2️⃣ Sum budget spent till quarter
    for row in metric_rows:
        mid = row["parent"]
        milestone = milestone_map.get(mid)
        if not milestone:
            continue

        ps = safe_parse_date(milestone.get("period_start"))
        if not ps or not (fy_start <= ps <= q_end):
            continue

        if row.get("title") == "Budget Spent":
            mtype = (row.get("type") or "").lower()
            if mtype == "int":
                val = row.get("data_int") or 0
            elif mtype == "float":
                val = row.get("data_float") or 0
            else:
                try:
                    val = float(row.get("data_string") or 0)
                except Exception:
                    val = 0

            overall_spent += float(val)

    # 3️⃣ Utilization percentage
    overall_utilization = (
        (overall_spent / overall_forecasted) * 100 if overall_forecasted else 0
    )
    return {
        "projects": full_projects,
        "total_budget_spent": total_budget_spent,
        "total_projects": len(full_projects),
        "overall_utilization_percent": round(overall_utilization, 2),
    }


@frappe.whitelist()
def compare_quarter_metrics_grant_forcast(grant_id, quarter_value, compare_with):
    # print("-----------> compare_quarter_metrics_grant called with grant_id:", grant_id, "quarter_value:", quarter_value, "compare_with:", compare_with)
    """
    Compare two quarters by aggregating SUM of four major readiness metrics.

    Metrics:
    1. Technology Readiness Level
    2. Market Readiness Level
    3. Commercial Readiness Level
    4. Social Impact Readiness Level
    """

    if not quarter_value or not compare_with:
        frappe.throw("quarter_value and compare_with are required.")

    if not grant_id or not quarter_value:
        frappe.throw("Grant ID and quarter_value are required")
    # print("Fetching projects for Grant:", grant_id, "Quarter/Year:", quarter_value)
    # ----------------------------
    # STEP 1: Fetch Projects
    # ----------------------------
    projects = frappe.get_list(
        "Grant Project",
        fields=[
            "name",
            "title",
            "alias",
            "start_date",
            "end_date",
            "lead_organization",
        ],
        filters={"grant": grant_id},
        limit_page_length=0,
    )
    project_ids = [p["name"] for p in projects]
    if not project_ids:
        return {"quarter": "", "compare_with": "", "metrics": {}}
    # print("Found Projects ------------------:", project_ids)

    # ----------------------------
    # Helpers
    # ----------------------------

    def fy_quarter_range(qval):
        """Return (start_date, end_date) for a given quarter value like Q2-2024-2025."""
        if not qval.startswith("Q"):
            frappe.throw("Quarter value must be like Q1-2024-2025")

        parts = qval.split("-")
        q = parts[0]  # Q1, Q2, Q3, Q4
        fy_start_year = int(parts[1])
        fy_end_year = int(parts[2])

        if q == "Q1":
            return date(fy_start_year, 4, 1), date(fy_start_year, 6, 30)
        elif q == "Q2":
            return date(fy_start_year, 7, 1), date(fy_start_year, 9, 30)
        elif q == "Q3":
            return date(fy_start_year, 10, 1), date(fy_start_year, 12, 31)
        elif q == "Q4":
            return date(fy_end_year, 1, 1), date(fy_end_year, 3, 31)
        else:
            frappe.throw("Invalid quarter code")

    # ----------------------------
    # Step 1: Convert the quarter ranges
    # ----------------------------
    curr_start, curr_end = fy_quarter_range(quarter_value)
    prev_start, prev_end = fy_quarter_range(compare_with)

    # ----------------------------
    # Step 2: Fetch milestones inside each quarter
    # ----------------------------
    all_milestones = frappe.get_list(
        "Grant Project Milestone",
        fields=["name", "period_start", "forecasted_amount"],
        filters={"project": ["in", project_ids]},
        order_by="creation desc",
        limit_page_length=0,
    )

    curr_m_ids = []
    prev_m_ids = []
    curr_forecasted_amounts = 0
    prev_forecasted_amounts = 0
    for m in all_milestones:
        ps = safe_parse_date(m.get("period_start"))
        if not ps:
            continue

        if curr_start <= ps <= curr_end:
            curr_m_ids.append(m["name"])
            print("Current milestone:", m.get("forecasted_amount"))
            curr_forecasted_amounts += (
                float(m.get("forecasted_amount")) if m.get("forecasted_amount") else 0
            )

        if prev_start <= ps <= prev_end:
            prev_m_ids.append(m["name"])
            prev_forecasted_amounts += (
                float(m.get("forecasted_amount")) if m.get("forecasted_amount") else 0
            )

    # ----------------------------
    # Step 3: Fetch metric values only for needed milestones
    # ----------------------------
    def fetch_metrics(milestone_ids):
        """Return metrics sum for 4 selected metrics."""
        if not milestone_ids:
            return {
                "Budget Spent": 0,
            }

        rows = frappe.get_all(
            "Grant Metric Value",
            fields=["parent", "title", "type", "data_string", "data_int", "data_float"],
            filters={"parent": ["in", milestone_ids]},
            limit_page_length=0,
        )
        # print("ROWS fetched for milestones:", rows)
        metrics_sum = {
            "Budget Spent": 0,
        }

        for r in rows:
            title = r.get("title")
            if title not in metrics_sum:
                continue

            # Extract numeric value
            mtype = (r.get("type") or "").lower()
            if mtype == "int":
                val = r.get("data_int") or 0
            elif mtype == "float":
                val = r.get("data_float") or 0
            else:
                # if string, try parsing
                try:
                    val = float(r.get("data_string") or 0)
                except Exception:
                    val = 0

            metrics_sum[title] += float(val)

        return metrics_sum

    curr_metrics = fetch_metrics(curr_m_ids)
    prev_metrics = fetch_metrics(prev_m_ids)

    curr_metrics["Forecasted Amount"] = curr_forecasted_amounts
    prev_metrics["Forecasted Amount"] = prev_forecasted_amounts

    print("Current Metrics:", curr_metrics)
    print("Previous Metrics:", prev_metrics)
    # ----------------------------
    # Step 4: Build comparison result
    # ----------------------------
    result = {}

    for metric in curr_metrics.keys():
        cur = curr_metrics[metric]
        prev = prev_metrics[metric]

        diff = cur - prev
        percent = 0
        if prev != 0:
            percent = (diff / prev) * 100

        result[metric] = {
            "current": cur,
            "previous": prev,
            "growth": diff,
            "growth_percent": round(percent, 2),
        }
    # ----------------------------
    # STEP 5: Calculate Fund Utilization (IMPORTANT)
    # ----------------------------

    curr_forecast = curr_metrics.get("Forecasted Amount", 0)
    prev_forecast = prev_metrics.get("Forecasted Amount", 0)

    curr_spent = curr_metrics.get("Budget Spent", 0)
    prev_spent = prev_metrics.get("Budget Spent", 0)

    # Utilization Rates
    curr_utilization = (curr_spent / curr_forecast) * 100 if curr_forecast else 0
    prev_utilization = (prev_spent / prev_forecast) * 100 if prev_forecast else 0

    # Utilization Growth (percentage-point change)
    utilization_growth = curr_utilization - prev_utilization

    result["Fund Utilization"] = {
        "current": round(curr_utilization, 2),
        "previous": round(prev_utilization, 2),
        "growth_percent": round(utilization_growth, 2),
    }
    return {"quarter": quarter_value, "compare_with": compare_with, "metrics": result}


@frappe.whitelist()
def compare_quarter_metrics_grant_project_spesific(
    grant_id, quarter_value, compare_with
):
    if not grant_id or not quarter_value or not compare_with:
        frappe.throw("grant_id, quarter_value and compare_with are required")

    # ------------------------------------------------
    # Helper: Quarter date range
    # ------------------------------------------------
    def fy_quarter_range(qval):
        if not qval.startswith("Q"):
            frappe.throw("Quarter value must be like Q1-2024-2025")

        parts = qval.split("-")
        q = parts[0]
        fy_start = int(parts[1])
        fy_end = int(parts[2])

        if q == "Q1":
            return date(fy_start, 4, 1), date(fy_start, 6, 30)
        elif q == "Q2":
            return date(fy_start, 7, 1), date(fy_start, 9, 30)
        elif q == "Q3":
            return date(fy_start, 10, 1), date(fy_start, 12, 31)
        elif q == "Q4":
            return date(fy_end, 1, 1), date(fy_end, 3, 31)
        else:
            frappe.throw("Invalid quarter")

    curr_start, curr_end = fy_quarter_range(quarter_value)
    prev_start, prev_end = fy_quarter_range(compare_with)

    # ------------------------------------------------
    # Step 1: Fetch projects under grant
    # ------------------------------------------------
    projects = frappe.get_list(
        "Grant Project",
        fields=["name"],
        filters={"grant": grant_id},
        limit_page_length=0,
    )

    if not projects:
        return []

    project_results = []

    # ------------------------------------------------
    # Step 2: Loop project-wise
    # ------------------------------------------------
    for p in projects:
        project_id = p["name"]

        milestones = frappe.get_list(
            "Grant Project Milestone",
            fields=["name", "period_start"],
            filters={"project": project_id},
            limit_page_length=0,
        )

        curr_m_ids = []
        prev_m_ids = []

        for m in milestones:
            ps = safe_parse_date(m.get("period_start"))
            if not ps:
                continue

            if curr_start <= ps <= curr_end:
                curr_m_ids.append(m["name"])

            if prev_start <= ps <= prev_end:
                prev_m_ids.append(m["name"])

        # ------------------------------------------------
        # Step 3: Metric aggregation helper
        # ------------------------------------------------
        def aggregate_metrics(milestone_ids):
            base = {
                "Technology Readiness Level": 0,
                "Market Readiness Level": 0,
                "Commercial Readiness Level": 0,
                "Social Impact Readiness Level": 0,
            }

            if not milestone_ids:
                return base

            rows = frappe.get_all(
                "Grant Metric Value",
                fields=["title", "type", "data_int", "data_float", "data_string"],
                filters={"parent": ["in", milestone_ids]},
                limit_page_length=0,
            )

            for r in rows:
                title = r.get("title")
                if title not in base:
                    continue

                mtype = (r.get("type") or "").lower()
                if mtype == "int":
                    val = r.get("data_int") or 0
                elif mtype == "float":
                    val = r.get("data_float") or 0
                else:
                    try:
                        val = float(r.get("data_string") or 0)
                    except Exception:
                        val = 0

                base[title] += float(val)

            return base

        curr_metrics = aggregate_metrics(curr_m_ids)
        prev_metrics = aggregate_metrics(prev_m_ids)

        metric_result = {}

        has_current_data = False
        has_previous_data = False

        for metric in curr_metrics:
            cur = float(curr_metrics.get(metric, 0) or 0)
            prev = float(prev_metrics.get(metric, 0) or 0)

            if cur > 0:
                has_current_data = True
            if prev > 0:
                has_previous_data = True

            # CASE 2: Only current exists
            if cur > 0 and prev == 0:
                growth = 0
                growth_percent = 0

            # CASE 4: Only previous exists
            elif cur == 0 and prev > 0:
                growth = -prev
                growth_percent = -100

            # CASE 3: Both exist
            elif cur > 0 and prev > 0:
                growth = cur - prev
                growth_percent = round((growth / prev) * 100, 2)

            # CASE 1: Neither exists
            else:
                growth = 0
                growth_percent = 0

            metric_result[metric] = {
                "current": cur,
                "previous": prev,
                "growth": growth,
                "growth_percent": growth_percent,
            }

        # ----------------------------
        # CASE 1: No data in both quarters → result = null
        # ----------------------------
        if not has_current_data and not has_previous_data:
            continue

        if has_current_data and not has_previous_data:
            project_results.append({"project": project_id, "result": None})
            continue

        # ----------------------------
        # Normal result
        # ----------------------------

        project_results.append(
            {
                "project": project_id,
                "result": {
                    "quarter": quarter_value,
                    "compare_with": compare_with,
                    "metrics": metric_result,
                },
            }
        )

    return project_results
