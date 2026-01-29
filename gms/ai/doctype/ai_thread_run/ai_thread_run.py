# Copyright (c) 2026, Triveous and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
from frappe.types import DF


class AIThreadRun(Document):
    thread: DF.Link
    parent_run: DF.Link
    query: DF.MarkdownEditor
    answer: DF.MarkdownEditor
    blocks: DF.JSON
