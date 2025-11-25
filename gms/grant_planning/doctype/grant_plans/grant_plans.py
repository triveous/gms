# Copyright (c) 2025, Triveous and contributors
# For license information, please see license.txt

# import frappe
from frappe import frappe
from frappe.model.document import Document

from gms.api.data_extractor import run_extraction_pipeline


def create_grant_projects_from_extracted_json(extracted):
	"""
	Input expected:
	{
	   "projects": [
	      {
	        "project_name": "Smartphone app...",
	        "y1": {
	            "q1": { "goals_deliverables": "...", "budget": "4 Cr." },
	            "q2": { "goals_deliverables": "...", "budget": "4 Cr." },
	            "q3": { "goals_deliverables": "...", "budget": "6 Cr." },
	            "q4": { "goals_deliverables": "...", "budget": "6 Cr." }
	        }
	      },
	      ...
	   ]
	}
	"""

	projects = extracted.get("projects", [])

	created_project_docs = []

	for project in projects:
		project_name = project.get("project_name")

		project_doc = frappe.get_doc(
			{
				"doctype": "Grant Project",
				"title": project_name,
				# "grant": grant_name
			}
		)

		project_doc.insert(ignore_permissions=True)
		# frappe.db.commit()

		created_project_docs.append(project_doc.name)

		y1 = project.get("y1", {})

		for quarter_key, quarter_data in y1.items():
			print(f"Processing {quarter_key} data: {quarter_data}")
			goals_text = quarter_data.get("goals_deliverables", "")
			budget = quarter_data.get("budget", "")

			# Each quarter becomes a "Goal Item"
			goal_doc = frappe.get_doc(
				{
					"doctype": "Grant Project Goals",
					"goal_item": goals_text,
					"budget_forecast": budget,
					"start_period": None,  # You can derive if needed
					"end_period": None,
					# "project": project_doc.name
				}
			)
			goal_doc.insert(ignore_permissions=True)
			# frappe.db.commit()

			milestone_doc = frappe.get_doc(
				{
					"doctype": "Grant Project Milestone",
					# "grant": grant_name,
					"due_date": None,  # You can infer quarter end date if needed
					"report": None,
					"updates": None,  # pushing detailed updates here
					"date_of_completion": None,
					"status": "Pending",
					"milestone_type": None,  # optional
				}
			)

			milestone_doc.insert(ignore_permissions=True)
			# frappe.db.commit()

	return created_project_docs


class GrantPlans(Document):
	def get_full_file_path(self, file_url):
		parts = file_url.strip("/").split("/", 2)  # ['private', 'files', 'filename']
		return frappe.get_site_path(parts[0], parts[1], parts[2])

	def before_save(self):
		file_path = self.get_full_file_path(self.upload_plan)

		structured_data = run_extraction_pipeline(file_path)
		print(structured_data)
		create_grant_projects_from_extracted_json(structured_data)

		frappe.msgprint("Data fetching task started successfully", alert=True)
