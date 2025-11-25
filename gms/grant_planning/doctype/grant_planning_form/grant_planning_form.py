# Copyright (c) 2025, Triveous and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from gms.api.data_extractor import run_extraction_pipeline


def create_grant_from_extracted_json(extracted, file_url):
	# extracted = parsed JSON from Gemini
	overview = extracted.get("overview", {})
	# Create new Grant DocType
	grant = frappe.get_doc(
		{
			"doctype": "Grant",
			"grant_name": overview.get("coe_name"),
			"approval_number": overview.get("approval_number"),
			"approved_amount": overview.get("approved_budget"),
			# "approved_on": overview.get("approved_on"),
			# "timeline_duration": overview.get("coe_timeline_duration"),
			"primary_investigators": overview.get("primary_co_primary_investigators"),
			# "lead_institutes": overview.get("lead_institutes"),
			# "key_industry_collaborators": "\n".join(overview.get("key_industry_collaborators", [])),
			"grant_type": "lfiud3mkbi",
			"grant_term": "fbi1i5urho",
		}
	)

	# Insert into DB
	grant.insert(ignore_permissions=True)
	# frappe.db.commit()

	# 2️⃣ Attach file to Grant (default attachment sidebar)
	file_doc = frappe.get_doc(
		{
			"doctype": "File",
			"file_url": file_url,
			"attached_to_doctype": "Grant",
			"attached_to_name": grant.name,
		}
	)

	file_doc.insert(ignore_permissions=True)
	# frappe.db.commit()

	return grant.name


class GrantPlanningForm(Document):
	def get_full_file_path(self, file_url):
		parts = file_url.strip("/").split("/", 2)  # ['private', 'files', 'filename']
		return frappe.get_site_path(parts[0], parts[1], parts[2])

	def before_save(self):
		file_url = self.upload_grant_document  # ← right value for File DocType

		file_path = self.get_full_file_path(file_url)  # only for reading file content

		structured_data = run_extraction_pipeline(file_path)
		create_grant_from_extracted_json(structured_data, file_url)

		frappe.msgprint(_("Data fetching task started successfully"), alert=True)
