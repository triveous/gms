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


@frappe.whitelist()
def get_single_grant_info(grant_id):
    if not grant_id:
        frappe.throw("Grant ID is required")

    grant = frappe.get_doc("Grant", grant_id)
    grant.check_permission("read")

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
    organization = frappe.get_value(
        "Grant Partner", grant.lead_organization, ["name", "title"], as_dict=True
    )
    grant_data["organization"] = organization or {}

    # ----------- Fetch Projects ----------
    projects = frappe.get_list(
        "Grant Project",
        fields=["name", "grant"],
        filters={"grant": grant_id},
        limit_page_length=0,
    )
    project_ids = [p["name"] for p in projects]

    project_count = {}
    for p in projects:
        project_count[p["grant"]] = project_count.get(p["grant"], 0) + 1

    # ----------- Fetch Milestones ----------
    milestones = []
    if project_ids:
        milestones = frappe.get_list(
            "Grant Project Milestone",
            fields=["name", "period_start", "forecasted_amount"],
            filters={"project": ["in", project_ids], "milestone_type": "Progress Update"},
            limit_page_length=0,
        )

    # ----------- Compute budget spent ----------
    milestone_ids = [m["name"] for m in milestones]
    total_budget = 0.0

    if milestone_ids:
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
            filters={"parent": ["in", milestone_ids]},
            limit_page_length=0,
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
        yearly_items.append(
            {"value": fy, "title": fy, "description": "This Year" if idx == 0 else None}
        )

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
    grant_data["total_projects"] = project_count.get(grant_id, 0)
    # Assign final result
    grant_data["budget_utilization"] = budget_utilization_list

    return grant_data


@frappe.whitelist(allow_guest=True)
def fetch_grant_dpr_files(grant_id, file_types=None, sort_by=None):
	"""
	Fetch DPR and milestone attachment files for a grant.

	Returns:
	- DPR file from Grant document
	- Milestone attachment files with types based on milestone type:
	  * "Planning Update" -> "Yearly Plans"
	  * "Progress Update" -> "Progress Report"

	Parameters:
	- grant_id: Grant ID
	- file_types: Comma-separated file types to filter (optional)
	- sort_by: Sort by "file_name" (optional)

	Returns: List of all files (DPR + milestone attachments) with file_types list
	"""
	if not grant_id:
		frappe.throw("Grant ID is required")

	# ----------------------------
	# STEP 1: Verify grant exists
	# ----------------------------
	grant = frappe.db.get_value(
		"Grant",
		grant_id,
		["name", "dpr"],
		as_dict=True,
	)
	if not grant:
		frappe.throw("Grant not found")

	files_list = []
	file_types_set = set()

	# Parse file_types filter
	file_types_filter = []
	if file_types:
		if isinstance(file_types, str):
			file_types_filter = [ft.strip() for ft in file_types.split(",")]
		else:
			file_types_filter = file_types

	# ----------------------------
	# STEP 2: Fetch DPR file if exists
	# ----------------------------
	dpr_file_name = grant.get("dpr")

	if dpr_file_name:
		file_doc = frappe.db.get_value(
			"File",
			{"file_url": dpr_file_name},
			["name", "file_name", "creation"],
			as_dict=True,
		)

		if file_doc:
			file_name = file_doc.get("file_name")
			creation_date = file_doc.get("creation")
			file_id = file_doc.get("name")

			# Parse creation date
			try:
				if isinstance(creation_date, str):
					uploaded_on = datetime.strptime(creation_date, "%Y-%m-%d %H:%M:%S.%f").strftime("%d-%m-%Y, %I:%M%p (IST)")
				else:
					uploaded_on = creation_date.strftime("%d-%m-%Y, %I:%M%p (IST)")
			except Exception:
				uploaded_on = str(creation_date)

			file_type = "DPR"
			file_types_set.add(file_type)

			# Apply file_type filter
			if file_types_filter and file_type not in file_types_filter:
				pass
			else:
				files_list.append({
					"file_id": file_id,
					"file_name": file_name,
					"uploaded_on": uploaded_on,
					"file_type": file_type,
					"milestone_id": None,
					"milestone_type": None,
					"download_link": dpr_file_name,
				})

	# ----------------------------
	# STEP 3: Fetch all projects for this grant
	# ----------------------------
	projects = frappe.get_all(
		"Grant Project",
		fields=["name"],
		filters={"grant": grant_id},
	)

	if projects:
		project_ids = [p["name"] for p in projects]

		# ----------------------------
		# STEP 4: Fetch all milestones for these projects with dates and uploaded_file
		# ----------------------------
		milestones = frappe.get_all(
			"Grant Project Milestone",
			fields=["name", "milestone_type", "period_start", "period_end", "uploaded_file"],
			filters={"project": ["in", project_ids], "milestone_type": "Progress Update"},
		)

		if milestones:
			milestone_type_map = {m["name"]: m.get("milestone_type") for m in milestones}
			milestone_dates_map = {
				m["name"]: {
					"start_date": m.get("period_start"),
					"end_date": m.get("period_end")
				} for m in milestones
			}
			
			# Map uploaded_file to milestone
			file_to_milestone_map = {m["uploaded_file"]: m["name"] for m in milestones if m.get("uploaded_file")}
			file_ids = list(file_to_milestone_map.keys())

			if file_ids:
				# ----------------------------
				# STEP 5: Fetch details for these unique files
				# ----------------------------
				milestone_files = frappe.get_all(
					"File",
					fields=["name", "file_name", "creation", "file_url"],
					filters={"name": ["in", file_ids]},
					order_by="creation desc",
				)

				# ----------------------------
				# STEP 6: Add milestone files with appropriate file types and dates
				# ----------------------------
				for file_doc in milestone_files:
					file_name = file_doc.get("file_name")
					creation_date = file_doc.get("creation")
					file_id = file_doc.get("name")
					file_url = file_doc.get("file_url")
					
					milestone_id = file_to_milestone_map.get(file_id)

					# Get milestone type and dates
					milestone_type = milestone_type_map.get(milestone_id)
					milestone_dates = milestone_dates_map.get(milestone_id, {})
					start_date = milestone_dates.get("start_date")
					end_date = milestone_dates.get("end_date")

					# Determine file_type based on milestone type
					if milestone_type == "Planning Update":
						file_type = "Yearly Plans"
					elif milestone_type == "Progress Update":
						file_type = "Progress Report"
					else:
						file_type = "Document"

					file_types_set.add(file_type)

					# Apply file_type filter
					if file_types_filter and file_type not in file_types_filter:
						continue

					# Parse creation date
					try:
						if isinstance(creation_date, str):
							uploaded_on = datetime.strptime(creation_date, "%Y-%m-%d %H:%M:%S.%f").strftime("%d-%m-%Y, %I:%M%p (IST)")
						else:
							uploaded_on = creation_date.strftime("%d-%m-%Y, %I:%M%p (IST)")
					except Exception:
						uploaded_on = str(creation_date)

					# Format dates
					try:
						if isinstance(start_date, str):
							start_date = start_date.split(" ")[0]  # Remove time if present
						else:
							start_date = str(start_date) if start_date else None
					except Exception:
						pass

					try:
						if isinstance(end_date, str):
							end_date = end_date.split(" ")[0]  # Remove time if present
						else:
							end_date = str(end_date) if end_date else None
					except Exception:
						pass

					files_list.append({
						"file_id": file_id,
						"file_name": file_name,
						"uploaded_on": uploaded_on,
						"file_type": file_type,
						"milestone_id": milestone_id,
						"milestone_type": milestone_type,
						"start_date": start_date,
						"end_date": end_date,
						"download_link": file_url,
					})

	# Define file type priority (DPR first, then Yearly Plans, then Progress Report)
	file_type_priority = {
		"DPR": 0,
		"Yearly Plans": 1,
		"Progress Report": 2,
	}

	# Helper function to parse uploaded_on date for sorting
	def parse_uploaded_date(date_str):
		try:
			# Format: "01-04-2025, 12:22PM (IST)"
			date_part = date_str.split(",")[0]  # "01-04-2025"
			time_part = date_str.split(",")[1].strip().replace(" (IST)", "")  # "12:22PM"
			return datetime.strptime(f"{date_part} {time_part}", "%d-%m-%Y %I:%M%p")
		except:
			return datetime.min

	# Apply sorting
	if sort_by == "file_name":
		# Sort by type priority first, then by file name
		files_list.sort(key=lambda x: (file_type_priority.get(x["file_type"], 3), x["file_name"].lower()))
	else:
		# Default: sort by type priority first, then by upload date (newest first)
		files_list.sort(key=lambda x: (file_type_priority.get(x["file_type"], 3), -parse_uploaded_date(x["uploaded_on"]).timestamp()))

	# Convert file_types_set to sorted list
	all_file_types = sorted(list(file_types_set))

	return {
		"grant_id": grant_id,
		"files": files_list,
		"total_count": len(files_list),
		"file_types": all_file_types,
	}



