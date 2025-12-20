# Copyright (c) 2025, Triveous and contributors
# For license information, please see license.txt

# import frappe

from frappe.model.document import Document


class AIConversation(Document):
    
    def set_history(self, messages: str):
        print(f"Settign history for {self.name}")
        self.messages = messages