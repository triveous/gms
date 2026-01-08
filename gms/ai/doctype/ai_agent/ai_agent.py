# Copyright (c) 2026, Triveous and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import json


class AIAgent(Document):
    agent_name: str
    instruction: str
    model: str
    model_settings: str

    add_current_time_instruction: bool
    add_user_name_instruction: bool

    enable_knowledgebase_tool: bool
    enable_reflect_tool: bool

    sub_agents: list["AIAgent"]

    @property
    def model_setting_dict(self):
        try:
            return json.load(self.model_settings) if self.model_settings else {}
        except Exception as e:
            frappe.log_error(
                f"Failed to load model setting for agent {self.agent_name}", e
            )
            return {}
