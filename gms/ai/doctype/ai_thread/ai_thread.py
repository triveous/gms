# Copyright (c) 2026, Triveous and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
from frappe.types import DF


class AIThread(Document):
    title: DF.Text
    first_answer: DF.MarkdownEditor
    last_run: DF.Link

    def has_default_title(self):
        return self.title is None or self.title == "" or self.title == "New Chat"
