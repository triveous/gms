import frappe

def get_context(context):
    if frappe.session.user == "Guest":
        frappe.local.response["type"] = "redirect"
        frappe.local.response["location"] = "/dashboard/login"
    else:
        frappe.local.response["type"] = "redirect"
        frappe.local.response["location"] = "/dashboard"
    return context