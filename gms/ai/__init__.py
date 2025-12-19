import frappe
import os
os.environ["GOOGLE_API_KEY"] = frappe.conf.get("google_api_key")