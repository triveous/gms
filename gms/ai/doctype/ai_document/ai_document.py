# Copyright (c) 2025, Triveous and contributors
# For license information, please see license.txt

import json

import frappe
from frappe.model.document import Document


class AIDocument(Document):
    def validate(self):
        # self.validate_metadata()
        pass

    def validate_metadata(self):
        if self.metadata:
            try:
                metadata_python = json.loads(self.metadata)
            except Exception:
                frappe.throw("Metadata should be a JSON Object")

            if not isinstance(metadata_python, dict):
                frappe.throw("Metadata should be a JSON Object")
