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


@frappe.whitelist(allow_guest=True)
def get_single_grant_info(grant_id):
	if not grant_id:
		frappe.throw("Grant ID is required")

	grant = frappe.get_doc("Grant", grant_id)

	grant_data = {
		"name": grant.name,
		"title": grant.title,
		"alias": grant.alias,
		"start_date": grant.start_date,
		"end_date": grant.end_date,
		"approved_amount": grant.approved_amount,
		"approval_number": grant.approval_identifier,
		"lead_organization": grant.lead_organization,
	}

	# Lead organization
	organization = frappe.db.get_value(
		"Grant Partner", grant.lead_organization, ["name", "title"], as_dict=True
	)
	grant_data["organization"] = organization or {}

	# ----------- Fetch Projects ----------
	projects = frappe.get_all(
		"Grant Project",
		fields=["name", "grant"],
		filters={"grant": grant_id},
	)
	project_ids = [p["name"] for p in projects]
 
	project_count = {}
	for p in projects:
		project_count[p["grant"]] = project_count.get(p["grant"], 0) + 1

	# ----------- Fetch Milestones ----------
	milestones = []
	if project_ids:
		milestones = frappe.get_all(
			"Grant Project Milestone",
			fields=["name", "period_start", "forecasted_amount"],
			filters={"project": ["in", project_ids]},
		)

	# ----------- Compute budget spent ----------
	milestone_ids = [m["name"] for m in milestones]
	total_budget = 0.0

	if milestone_ids:
		metric_rows = frappe.get_all(
			"Grant Metric Value",
			fields=["title", "type", "data_string", "data_int", "data_float", "data_boolean"],
			filters={"parent": ["in", milestone_ids]},
		)

		for row in metric_rows:
			if row.get("title") != "Budget Spent":
				continue

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
				value = float(raw) if raw not in (None, "") else 0.0
			except Exception:
				value = 0.0

			total_budget += value

	grant_data["budget_spent"] = total_budget

	# ----------- Build Quarters List ----------
	quarter_groups = {}  # fy_label -> dict(value -> item_with_sortinfo)
	fy_start_map = {}  # fy_label -> fy_start (int)

	for m in milestones:
		ps = m.get("period_start")
		dt = safe_parse_date(ps)
		if not dt:
			continue

		q, fy_label, title, value, quarter_start, fy_start = quarter_info_from_date(dt)

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
		yearly_items.append({"value": fy, "title": fy, "description": "This Year" if idx == 0 else None})

	if yearly_items:
		quarters_list.append({"label": "Yearly Wise", "items": yearly_items})

	grant_data["quartersList"] = quarters_list

	# --------------------- BUDGET UTILIZATION PER QUARTER ---------------------
	budget_by_quarter = {}  # quarter_key -> {quarterStartDate, budgetSpent, forecastedAmount}

	for m in milestones:
		ps = m.get("period_start")
		dt = safe_parse_date(ps)
		if not dt:
			continue

		# Extract quarter info
		q, fy_label, title, quarter_key, quarter_start, fy_start = quarter_info_from_date(dt)

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
			fields=["title", "type", "data_string", "data_int", "data_float", "data_boolean"],
			filters={"parent": m["name"]},
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
	grant_data["total_projects"] = project_count.get(grant_id, 0)
	# Assign final result
	grant_data["budget_utilization"] = budget_utilization_list

	return grant_data


@frappe.whitelist(allow_guest=True)
def get_grant_kpi_metrics_by_quarter(grant_id, quarter_value):
    if not grant_id or not quarter_value:
        frappe.throw("Grant ID and quarter_value are required")

    # ----------------------------
    # Utility: Quarter range
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
    # STEP 1: Fetch all KPI Metric docs for grant
    # ----------------------------
    kpi_docs = frappe.get_all(
        "Grant KPI Metrics",
        fields=[
            "name",
            "title",
            "grant",
            "period_start",
            "period_end",
            "kpi_computed_at",
            "creation",
        ],
        filters={"grant": grant_id},
        order_by="creation desc",
    )
    print("kpi_docs ----> ",kpi_docs)
 
    if not kpi_docs:
        return {
            "grant": grant_id,
            "quarter_value": quarter_value,
            "kpis": [],
        }

    # ----------------------------
    # STEP 2: Filter by quarter / FY
    # ----------------------------
    filtered_kpi_ids = []

    if quarter_value.startswith("Q"):
        try:
            parts = quarter_value.split("-")
            q = parts[0]
            fy_start_year = int(parts[1])
        except Exception:
            frappe.throw("Invalid quarter_value format")

        start_date, end_date = quarter_start_end(q, fy_start_year)
    else:
        try:
            fy_start_year = int(quarter_value.split("-")[0])
            fy_end_year = int(quarter_value.split("-")[1])
        except Exception:
            frappe.throw("Invalid quarter_value format")

        start_date = date(fy_start_year, 4, 1)
        end_date = date(fy_end_year, 3, 31)

    for kpi in kpi_docs:
        ps = safe_parse_date(kpi.get("period_start"))
        if ps and start_date <= ps <= end_date:
            filtered_kpi_ids.append(kpi["name"])

    if not filtered_kpi_ids:
        return {
            "grant": grant_id,
            "quarter_value": quarter_value,
            "kpis": [],
        }

    # ----------------------------
    # STEP 3: Fetch KPI Metric Values (child table)
    # ----------------------------
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
        filters={
            "parenttype": "Grant KPI Metrics",
            "parent": ["in", filtered_kpi_ids],
        },
    )

    # ----------------------------
    # STEP 4: Group KPI values per KPI document
    # ----------------------------
    metrics_map = {}

    for row in metric_rows:
        pid = row["parent"]
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

        metrics_map.setdefault(pid, {})

        # SPECIAL HANDLING: Highlights / Lowlights
        if title in ("High lights", "Low lights"):
            metrics_map[pid].setdefault(title, [])
            if value:
                metrics_map[pid][title].append(value)
        else:
            metrics_map[pid][title] = value

    # ----------------------------
    # STEP 5: Final response structure
    # ----------------------------
    result = []

    for kpi in kpi_docs:
        if kpi["name"] not in filtered_kpi_ids:
            continue

        result.append(
            {
                "kpi_id": kpi["name"],
                "title": kpi.get("title"),
                "period_start": kpi.get("period_start"),
                "period_end": kpi.get("period_end"),
                "kpi_computed_at": kpi.get("kpi_computed_at"),
                "metrics": metrics_map.get(kpi["name"], {}),
            }
        )

    return {
        "grant": grant_id,
        "quarter_value": quarter_value,
        "kpis": result,
    }