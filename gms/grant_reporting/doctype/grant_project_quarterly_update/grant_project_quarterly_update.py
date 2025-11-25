# Copyright (c) 2025, Triveous and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from gms.api.data_extractor import run_extraction_pipeline


def create_grant_project_reports(extracted):
	"""
	Creates Grant Project Report from extracted monthly update JSON.
	Links to existing Grant Project using initiative_program_workstream_names.
	"""

	reports_data = extracted.get("quarterly_updates_and_assessment", [])

	created_reports = []

	for row in reports_data:
		project_name = row.get("workstream_names")
		print("KEY ACTIVITIES:------>", row.get("key_activities_performed", ""))
		# Find project
		project = frappe.db.get_value("Grant Project", {"title": project_name}, ["name", "title"])
		print("PROJECT NAME:------>", project_name)
		if not project:
			frappe.logger().warning(f"[Grant Report] Project not found: {project_name}")
			continue

		print("PROJECT FOUND:------>", project)

		# Create report
		report_doc = frappe.get_doc(
			{
				"doctype": "Grant Project Report",
				"project": project[0],
				"key_activities_performed": row.get("key_activities_performed", ""),
				"highlights": row.get("high_lights", ""),
				"lowlight": row.get("low_lights", ""),
				"pregress": row.get("overall_progress_in_percentage", ""),
				"milestone_achieved": row.get("milestones_achieved_if_any", ""),
				"trl": row.get("technology_readiness_level_trl", ""),
				"mrl": "",
				"crl": "",
				"sirl": "",
				"impact_created": row.get("impact_created_if_any_links_to_calculations_and_evidences", ""),
				"budget_spent": row.get("budget_spent_if_any", ""),
				"additional_comments": row.get(
					"additional_comments_by_initiatives_program_workstream_owner", ""
				),
				# "update_date": nowdate(),
			}
		)

		report_doc.insert(ignore_permissions=True)
		frappe.db.commit()

		created_reports.append(report_doc.name)

	return created_reports


class GrantProjectQuarterlyUpdate(Document):
	def get_full_file_path(self, file_url):
		parts = file_url.strip("/").split("/", 2)  # ['private', 'files', 'filename']
		return frappe.get_site_path(parts[0], parts[1], parts[2])

	def before_save(self):
		file_path = self.get_full_file_path(self.upload_quarterly_update)

		structured_data = run_extraction_pipeline(file_path)
		print(structured_data)
		create_grant_project_reports(structured_data)

		frappe.msgprint("Data fetching task started successfully", alert=True)
