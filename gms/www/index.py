import frappe

def get_context(context):
    frappe.local.response["type"] = "redirect"
    frappe.local.response["location"] = "dashboard"
    return context