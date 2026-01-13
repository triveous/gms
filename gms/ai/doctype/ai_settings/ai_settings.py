# Copyright (c) 2026, Triveous and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class AISettings(Document):
    def validate(self):
        if (
            self.contextualization_prompt
            and "{{chunk}}" not in self.contextualization_prompt
        ):
            frappe.throw("Contextualization Prompt should have placeholder {chunk}}")
