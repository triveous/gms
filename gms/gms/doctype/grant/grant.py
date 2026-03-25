# Copyright (c) 2025, Triveous and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _


class Grant(Document):
    def validate(self):
        self.ensure_contributors()
        self.ensure_unique_grantee()

    def ensure_contributors(self):
        if not any(
            map(lambda d: d.get("contribution_type") == "Funder", self.contributors)
        ):
            frappe.throw(_("At least one funder is required."))

    def ensure_unique_grantee(self):
        """
        Enforce the rule that an organization can only be associated with one Grant as a Grantee.
        Validates that any organization assigned as a 'Grantee' in this Grant
        is not already assigned as a 'Grantee' in any other Grant, and is only
        added once within this Grant's contributors table.
        """
        grantees = [d.organization for d in self.contributors if d.get("contribution_type") == "Grantee" and d.get("organization")]
        
        # Check for duplicates within the current grant
        if len(grantees) != len(set(grantees)):
            frappe.throw(_("An organization can only be added once as a Grantee in this Grant."))

        for org in grantees:
            existing_grant = frappe.db.get_value(
                "Grant Contributor",
                {
                    "organization": org,
                    "contribution_type": "Grantee",
                    "parent": ("!=", self.name) if self.name else ("!=", ""),
                    "parenttype": "Grant"
                },
                "parent"
            )
            if existing_grant:
                frappe.throw(_("Organization {0} is already associated as a Grantee with Grant {1}. An organization can only be a Grantee for one Grant.").format(
                    frappe.bold(org), frappe.bold(existing_grant)
                ))
