# Copyright (c) 2025, Triveous and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _


class Grant(Document):
    def validate(self):
        self.ensure_contributors()

    def ensure_contributors(self):
        if not any(
            map(lambda d: d.get("contribution_type") == "Funder", self.contributors)
        ):
            frappe.throw(_("At least one funder is required."))
