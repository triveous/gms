def init_ai():
    import os

    import frappe

    os.environ["GOOGLE_API_KEY"] = frappe.conf.get("google_api_key")


init_ai()
