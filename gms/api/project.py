from datetime import date, datetime

import frappe


def safe_parse_date(ps):
    if not ps:
        return None

    if isinstance(ps, datetime):
        return ps.date()
    if isinstance(ps, date):
        return ps

    if isinstance(ps, str):
        s = ps.strip()
        if s == "":
            return None
        if " " in s:
            s = s.split(" ")[0]

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


def quarter_info_from_date(dt):
    """
    Given a datetime.date dt, return:
      - quarter (Q1..Q4)
      - fy_label (e.g. "2025-2026")
      - title (e.g. "Q2 Jul-Sep 2025")
      - value (e.g. "Q2-2025-2026")
      - quarter_start_date (date) used for sorting within FY
      - fy_start (int) used for sorting FYs
    """
    year = dt.year
    month = dt.month

    if month in (4, 5, 6):  # Q1 Apr-Jun
        q = "Q1"
        fy_start = year
        fy_end = year + 1
        title = f"Q1 Apr-Jun {fy_start}"
        quarter_start = date(year, 4, 1)
    elif month in (7, 8, 9):  # Q2 Jul-Sep
        q = "Q2"
        fy_start = year
        fy_end = year + 1
        title = f"Q2 Jul-Sep {fy_start}"
        quarter_start = date(year, 7, 1)
    elif month in (10, 11, 12):  # Q3 Oct-Dec
        q = "Q3"
        fy_start = year
        fy_end = year + 1
        title = f"Q3 Oct-Dec {fy_start}"
        quarter_start = date(year, 10, 1)
    else:  # Jan-Mar -> Q4, belongs to previous FY start
        q = "Q4"
        fy_start = year - 1
        fy_end = year
        title = f"Q4 Jan-Mar {fy_end}"
        quarter_start = date(year, 1, 1)

    fy_label = f"{fy_start}-{fy_end}"
    value = f"{q}-{fy_label}"  # e.g. Q2-2025-2026

    return q, fy_label, title, value, quarter_start, fy_start


@frappe.whitelist()
def get_project_details(project_id):
    """
    Return ALL data for a single project:
    - All milestones
    - Each milestone's forecasted amount
    - All metric values for each milestone
    - Total budget spent (sum of all milestone Budget Spent)
    """

    print("get_project_details called with project_id:", project_id)

    if not project_id:
        frappe.throw("Project ID is required")

    # ----------------------------
    # STEP 1: Fetch the project
    # ----------------------------
    project = frappe.get_doc(
        "Grant Project",
        project_id,
        ["name", "title", "alias", "start_date", "end_date", "lead_organization"],
    ).as_dict()

    if not project:
        frappe.throw("Invalid project ID")

    if project and project.get("lead_organization"):
        project["lead_organization"] = frappe.get_value(
            "Grant Partner", project["lead_organization"], "title"
        )
    else:
        project["lead_organization"] = None

    print("Found Project:", project)

    # ----------------------------
    # STEP 2: Fetch ALL milestones for this project
    # ----------------------------
    milestone = frappe.get_list(
        "Grant Project Milestone",
        fields=[
            "name",
            "project",
            "title",
            "period_start",
            "creation",
            "forecasted_amount",
        ],
        filters={"project": project_id},
        order_by="creation desc",
        limit=1,
    )
    print("Found Milestones for project:", milestone)

    # ----------------------------
    # STEP 4: Build final project object (same format as your original API)
    # ----------------------------
    project_obj = {
        **project,
        "last_updated": milestone[0].get("creation") if milestone else None,
        # "milestones": []
    }
    print("Building project object:", project_obj)

    # ----------- Fetch Milestones ----------
    milestones = []
    if project_id:
        milestones = frappe.get_list(
            "Grant Project Milestone",
            fields=["name", "period_start", "forecasted_amount"],
            filters={"project": project_id},
        )
    # ----------- Build Quarters List ----------
    quarter_groups = {}  # fy_label -> dict(value -> item_with_sortinfo)
    fy_start_map = {}  # fy_label -> fy_start (int)
    quarter_wise_overall_progress = []  # quarter_value -> overall_progress float
    for m in milestones:
        ps = m.get("period_start")
        dt = safe_parse_date(ps)
        if not dt:
            continue

        q, fy_label, title, value, quarter_start, fy_start = quarter_info_from_date(dt)

        metric_rows = frappe.get_all(
            "Grant Metric Value",
            fields=["title", "data_float"],
            filters={"parent": m["name"]},
            limit_page_length=0,
        )
        overall_progress = 0.0
        for row in metric_rows:
            row_title = (row.get("title") or "").strip()
            try:
                val = (
                    row.get("data_float")
                    if row.get("data_float") not in (None, "")
                    else 0.0
                )
            except Exception:
                val = 0.0
            if row_title == "Overall Progress":
                overall_progress = val

        quarter_wise_overall_progress.append(
            {"quarter": value, "overall_progress": overall_progress}
        )

        fy_start_map[fy_label] = fy_start
        # ensure unique quarters per FY: use dict keyed by 'value'
        quarter_groups.setdefault(fy_label, {})
        if value not in quarter_groups[fy_label]:
            quarter_groups[fy_label][value] = {
                "value": value,
                "title": title,
                "description": None,
                "_sort": quarter_start,  # temp field for sorting
            }

    # sort FYs by fy_start desc (latest FY first)
    sorted_fys = sorted(fy_start_map.items(), key=lambda kv: kv[1], reverse=True)
    sorted_fy_labels = [kv[0] for kv in sorted_fys]

    quarters_list = []

    # Current year section (latest FY)
    if sorted_fy_labels:
        current_fy = sorted_fy_labels[0]
        # sort quarters inside FY by quarter_start descending
        items = list(quarter_groups.get(current_fy, {}).values())
        items.sort(key=lambda x: x["_sort"], reverse=True)
        # drop _sort before returning
        for it in items:
            it.pop("_sort", None)
        quarters_list.append({"label": f"Current year ({current_fy})", "items": items})

    # Past FY sections
    for fy in sorted_fy_labels[1:]:
        items = list(quarter_groups.get(fy, {}).values())
        items.sort(key=lambda x: x["_sort"], reverse=True)
        for it in items:
            it.pop("_sort", None)
        quarters_list.append({"label": fy, "items": items})

    # Yearly Wise
    yearly_items = []
    for idx, fy in enumerate(sorted_fy_labels):
        yearly_items.append(
            {"value": fy, "title": fy, "description": "This Year" if idx == 0 else None}
        )

    if yearly_items:
        quarters_list.append({"label": "Yearly Wise", "items": yearly_items})

    project_obj["quartersList"] = quarters_list
    project_obj["quarterWiseOverallProgress"] = quarter_wise_overall_progress
    # --------------------- BUDGET UTILIZATION PER QUARTER ---------------------
    budget_by_quarter = {}  # quarter_key -> {quarterStartDate, budgetSpent, forecastedAmount}

    for m in milestones:
        ps = m.get("period_start")
        dt = safe_parse_date(ps)
        if not dt:
            continue

        # Extract quarter info
        q, fy_label, title, quarter_key, quarter_start, fy_start = (
            quarter_info_from_date(dt)
        )

        # Initialize quarter bucket if not exists
        if quarter_key not in budget_by_quarter:
            budget_by_quarter[quarter_key] = {
                "quarter": quarter_key,
                "title": title,  # "Q2 Jul-Sep 2025"
                "quarterStartDate": quarter_start,
                "budgetSpent": 0.0,
                "forecastedAmount": 0.0,
            }

        # -------------------------------------------------------------------
        # 1️⃣ BUDGET SPENT (comes from Grant Metric Value)
        # -------------------------------------------------------------------
        metric_rows = frappe.get_all(
            "Grant Metric Value",
            fields=[
                "title",
                "type",
                "data_string",
                "data_int",
                "data_float",
                "data_boolean",
            ],
            filters={"parent": m["name"]},
            limit_page_length=0,
        )

        milestone_budget_spent = 0.0

        for row in metric_rows:
            title = (row.get("title") or "").strip()
            mtype = (row.get("type") or "").lower()

            raw = (
                row.get("data_int")
                if mtype == "int"
                else row.get("data_float")
                if mtype == "float"
                else row.get("data_boolean")
                if mtype == "boolean"
                else row.get("data_string")
            )

            try:
                val = float(raw) if raw not in (None, "") else 0.0
            except Exception:
                val = 0.0

            # Only budget spent comes from metric table
            if title == "Budget Spent":
                milestone_budget_spent += val

        # Add to quarter bucket
        budget_by_quarter[quarter_key]["budgetSpent"] += milestone_budget_spent

        # -------------------------------------------------------------------
        # 2️⃣ FORECASTED AMOUNT (comes directly from Project Milestone)
        # -------------------------------------------------------------------
        milestone_forecasted = float(m.get("forecasted_amount") or 0.0)

        # Add to quarter bucket
        budget_by_quarter[quarter_key]["forecastedAmount"] += milestone_forecasted

    # -------------------------------------------
    # Sort quarters by quarterStartDate DESC
    # -------------------------------------------
    budget_utilization_list = list(budget_by_quarter.values())
    budget_utilization_list.sort(key=lambda x: x["quarterStartDate"], reverse=True)

    # Convert quarterStartDate → string format
    for item in budget_utilization_list:
        item["quarterStartDate"] = item["quarterStartDate"].strftime("%Y-%m-%d")

    # Assign final result
    project_obj["budget_utilization"] = budget_utilization_list

    return {
        "project": project_obj,
    }


@frappe.whitelist()
def get_grant_projects_by_quarter(project_id, quarter_value):
    print(
        "get_grant_projects_by_quarter called with project_id:",
        project_id,
        "and quarter_value:",
        quarter_value,
    )

    if not project_id or not quarter_value:
        frappe.throw("Project ID and quarter_value are required")

    # ----------------------------
    # STEP 1: Fetch this single project
    # ----------------------------
    project = frappe.get_value(
        "Grant Project",
        project_id,
        ["name", "title", "alias", "start_date", "end_date", "lead_organization"],
        as_dict=True,
    )
    if not project:
        frappe.throw("Project not found")

    project_id = project["name"]

    # ----------------------------
    # STEP 2: Fetch ALL Milestones of this project
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
        filters={"project": project_id},
        order_by="creation desc",
        limit_page_length=0,
    )

    print("Found Milestones:", [m["name"] for m in milestones])
    # milestone_ids = [m["name"] for m in milestones]

    # ----------------------------
    # Utility: Quarter Range
    # ----------------------------
    def quarter_start_end(q, fy_start_year):
        fy_end_year = fy_start_year + 1
        if q == "Q1":
            return date(fy_start_year, 4, 1), date(fy_start_year, 6, 30)
        if q == "Q2":
            return date(fy_start_year, 7, 1), date(fy_start_year, 9, 30)
        if q == "Q3":
            return date(fy_start_year, 10, 1), date(fy_start_year, 12, 31)
        if q == "Q4":
            return date(fy_end_year, 1, 1), date(fy_end_year, 3, 31)
        return None, None

    # ----------------------------
    # STEP 3: Filter milestones by quarter/year
    # ----------------------------
    filtered_milestone_ids = []

    if quarter_value.startswith("Q"):
        # Quarterly filter: Q2-2025-2026
        try:
            parts = quarter_value.split("-")
            q = parts[0]  # Q1, Q2, Q3, Q4
            fy_start_year = int(parts[1])
            # parts[2] is fy_end_year not needed
        except Exception:
            frappe.throw("Invalid quarter_value format")

        start_date, end_date = quarter_start_end(q, fy_start_year)

        for m in milestones:
            ps = m.get("period_start")
            ps_date = safe_parse_date(ps)
            if ps_date and start_date <= ps_date <= end_date:
                filtered_milestone_ids.append(m["name"])

    else:
        # Yearly filter: 2025-2026
        fy_start_year = int(quarter_value.split("-")[0])
        fy_end_year = int(quarter_value.split("-")[1])

        start_date = date(fy_start_year, 4, 1)
        end_date = date(fy_end_year, 3, 31)

        for m in milestones:
            ps = m.get("period_start")
            ps_date = safe_parse_date(ps)
            if ps_date and start_date <= ps_date <= end_date:
                filtered_milestone_ids.append(m["name"])
    print("Filtered Milestone IDs for quarter_value", filtered_milestone_ids)
    milestone_map = {
        m["name"]: m for m in milestones if m["name"] in filtered_milestone_ids
    }
    artifacts = frappe.get_all(
        "Grant Project Milestone Artifact",
        fields=["parent", "title", "link"],
        filters={"parent": ["in", filtered_milestone_ids]},
        limit_page_length=0,
    )

    print("-----------------------> ", artifacts)
    # ----------------------------
    # STEP 4: Fetch Metric Values for Filtered Milestones
    # ----------------------------
    milestone_metrics = {}
    budget_spent_per_milestone = {}
    total_budget_spent = 0

    if filtered_milestone_ids:
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
            filters={"parent": ["in", filtered_milestone_ids]},
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

        milestone_metrics.setdefault(mid, {})

        # ----------------------------
        # SPECIAL HANDLING: Highlights / Lowlights
        # ----------------------------
        if title in ("High lights", "Low lights"):
            milestone_metrics[mid].setdefault(title, [])
            if value:
                milestone_metrics[mid][title].append(value)
        else:
            milestone_metrics[mid][title] = value

        # Calculate Budget Spent
        if title == "Budget Spent":
            try:
                numeric = float(value) if value else 0
            except Exception:
                numeric = 0
            budget_spent_per_milestone[mid] = (
                budget_spent_per_milestone.get(mid, 0) + numeric
            )
            total_budget_spent += numeric

    # ----------------------------
    # STEP 5: Fetch Partners & Contributors
    # ----------------------------

    partners_map = {}
    contributors_map = {}

    if filtered_milestone_ids:
        # Fetch Partners
        partner_rows = frappe.get_all(
            "Grant Project Milestone Partner",
            fields=["parent", "partner", "responsibility"],
            filters={
                "parent": ["in", filtered_milestone_ids],
                "parenttype": "Grant Project Milestone",
                "parentfield": "partners",
            },
            limit_page_length=0,
        )

        # Fetch Contributors
        contributor_rows = frappe.get_all(
            "Grant Project Milestone Contributor",
            fields=["parent", "team_member", "role"],
            filters={
                "parent": ["in", filtered_milestone_ids],
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
            partners = frappe.get_all(
                "Grant Partner",
                fields=["name", "title"],
                filters={"name": ["in", list(partner_ids)]},
                limit_page_length=0,
            )
            partner_title_map = {p["name"]: p["title"] for p in partners}

        # Fetch Grant Member titles
        if member_ids:
            members = frappe.get_all(
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
    # STEP 6: Prepare final single project result
    # ----------------------------
    final_project = {**project, "milestone": {}}

    for m in milestones:
        if m["name"] not in filtered_milestone_ids:
            continue

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
                    "contributor": contributors[i] if i < len(contributors) else None,
                }
            )
        final_project["milestone"] = {
            "name": mid,
            "milestone_title": m.get("title"),
            "period_start": m.get("period_start"),
            "last_updated": m.get("creation"),
            "forecasted_amount": m.get("forecasted_amount"),
            "artifacts": artifacts,
            "metrics": milestone_metrics.get(mid, {}),
            "partners_and_team_members": partners_and_contributors,
        }

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
        "project": final_project,
        "overall_utilization_percent": round(overall_utilization, 2),
    }


@frappe.whitelist(allow_guest=True)
def compare_quarter_metrics_grant(project_id, quarter_value, compare_with):
    print(
        "-----------> compare_quarter_metrics_grant called with project_id:",
        project_id,
        "quarter_value:",
        quarter_value,
        "compare_with:",
        compare_with,
    )
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

    if not project_id or not quarter_value:
        frappe.throw("Project ID and quarter_value are required")

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
        filters={"project": project_id},
        order_by="creation desc",
        limit_page_length=0,
    )

    curr_m_ids = []
    prev_m_ids = []
    curr_forecasted_amounts = 0
    prev_forecasted_amounts = 0
    for m in all_milestones:
        ps = safe_parse_date(m.get("period_start"))
        fa = float(m.get("forecasted_amount")) if m.get("forecasted_amount") else 0
        if not ps:
            continue

        if curr_start <= ps <= curr_end:
            curr_m_ids.append(m["name"])
            curr_forecasted_amounts += fa

        if prev_start <= ps <= prev_end:
            prev_m_ids.append(m["name"])
            prev_forecasted_amounts += fa

    # ----------------------------
    # Step 3: Fetch metric values only for needed milestones
    # ----------------------------
    def fetch_metrics(milestone_ids):
        """Return metrics sum for 4 selected metrics."""
        if not milestone_ids:
            return {
                "Technology Readiness Level": 0,
                "Market Readiness Level": 0,
                "Commercial Readiness Level": 0,
                "Social Impact Readiness Level": 0,
                "Budget Spent": 0,
                "Impact Created": 0,
                "AI Breakthroughs": 0,
            }

        rows = frappe.get_all(
            "Grant Metric Value",
            fields=["parent", "title", "type", "data_string", "data_int", "data_float"],
            filters={"parent": ["in", milestone_ids]},
            limit_page_length=0,
        )

        metrics_sum = {
            "Technology Readiness Level": 0,
            "Market Readiness Level": 0,
            "Commercial Readiness Level": 0,
            "Social Impact Readiness Level": 0,
            "Budget Spent": 0,
            "Impact Created": 0,
            "AI Breakthroughs": 0,
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
