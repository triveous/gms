import json
import re
import frappe
import frappe.sessions

no_cache = 1

SCRIPT_TAG_PATTERN = re.compile(r"\<script[^<]*\</script\>")
CLOSING_SCRIPT_TAG_PATTERN = re.compile(r"</script\>")

def get_context(context):
    """
    Get context for index.html template.
    Injects Frappe boot data and CSRF token for React app.
    """
    # Get CSRF token first to ensure session is initialized
    csrf_token = frappe.sessions.get_csrf_token()
    frappe.db.commit()  # nosemgrep

    if frappe.session.user == "Guest":
        boot = frappe.website.utils.get_boot_data()
    else:
        try:
            boot = frappe.sessions.get()
        except Exception as e:
            raise frappe.SessionBootFailed from e

    # CRITICAL: SET the fresh token INTO boot, don't extract from boot
    if "session" not in boot or not isinstance(boot["session"], dict):
        boot["session"] = {}
    boot["session"]["csrf_token"] = csrf_token  # SET, don't extract
    boot["csrf_token"] = csrf_token  # Also set at root level

    # Follow Raven's pattern: encode boot as JSON string
    boot_json = frappe.as_json(boot, indent=None, separators=(",", ":"))
    boot_json = SCRIPT_TAG_PATTERN.sub("", boot_json)
    boot_json = CLOSING_SCRIPT_TAG_PATTERN.sub("", boot_json)
    boot_json = json.dumps(boot_json)

    context.update({
        "build_version": frappe.utils.get_build_version(),
        "boot": boot_json,  # Pass JSON string
        "csrf_token": csrf_token,
    })

    context["app_name"] = "AIKAM"
    # context["favicon"] = "/assets/your_app/favicon.ico"

    return context