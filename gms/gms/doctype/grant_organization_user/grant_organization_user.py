# Copyright (c) 2026, Triveous and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class GrantOrganizationUser(Document):
    def validate(self):
        self.ensure_single_membership()
        self.validate_other_admins_exist()

    def ensure_single_membership(self):
        existing_member = frappe.db.exists(
            "Grant Organization User",
            {
                "user": self.user,
                "name": ["!=", self.name],
            },
        )
        if existing_member:
            frappe.throw(
                f"User {self.user} is already a member of another organization."
            )

    def validate_other_admins_exist(self):
        if self.has_value_changed("is_admin") and not self.is_admin:
            other_admins = frappe.db.count(
                "Grant Organization User",
                {
                    "organization": self.organization,
                    "is_admin": True,
                    "name": ["!=", self.name],
                },
            )
            if other_admins == 0:
                frappe.throw(
                    _(
                        "You cannot delete the last admin of the organization. Please assign another user as the admin, or delete the organization instead."
                    )
                )
