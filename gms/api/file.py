import frappe
from frappe.core.doctype.file.file import File


def on_update(doc: File, method):
    create_ai_document(doc)


def on_after_delete(doc: File, method):
    delete_ai_document(doc)


def create_ai_document(doc: File):
    # Automatically create a AI Document when PDF File
    # is attached to "Grant","Grant Project","Grant Project Milestone"

    if (
        doc.attached_to_doctype
        not in [
            "Grant",
            "Grant Project",
            "Grant Project Milestone",
        ]
        or doc.attached_to_name is None
    ):
        return

    # Only Allow for PDF Ingestion for now
    if doc.file_type != "PDF":
        return False

    ai_document = frappe.get_doc({"doctype": "AI Document", "file": doc.name})
    ai_document.insert(ignore_permissions=True)


def delete_ai_document(doc: File):
    # Automatically create a AI Document if the deleted file was linked

    try:
        if frappe.db.exists("AI Document", {"file": doc.name}):
            ai_document = frappe.get_doc("AI Document", {"file": doc.name})
            frappe.delete_doc("AI Document", ai_document.name)
            frappe.log(f"Deleted AI Document {ai_document}")
    except Exception as e:
        frappe.throw("Failed to delete relevant AI Document", exc=e)
