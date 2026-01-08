# Copyright (c) 2026, Triveous and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class AISubAgent(Document):
    agent: str
    tool_name: str
    tool_description: str
