from io import BytesIO

import frappe
from frappe.core.doctype.file.file import File
from gms.ai.agents.base.knowledge_base import KnowledgeBase


def on_file_update(doc: File, method):
    ingest_file_to_kb_if_needed(doc)


def on_file_deleted(doc: File, method):
    remove_document_if_needed(doc)


def ingest_file_to_kb_if_needed(doc: File):
    # Allow Doctype from which ingestion needs to be done and id exists as well
    if (
        doc.attached_to_doctype
        not in [
            "Grant",
            "Grant Project",
            "Grant Project Milestone",
        ]
        or doc.attached_to_name is None
    ):
        return False

    # Only Allow for PDF Ingestion for now
    if doc.file_type != "PDF":
        return False

    ingest_to_kb(file_id=doc.name)


def ingest_to_kb(file_id):
    doc = frappe.get_doc("File", file_id)

    doc_meta = {"file_id": file_id}
    root_path = "Home/IndexedFiles"

    if doc.attached_to_doctype == "Grant":
        grant_id = doc.attached_to_name
        doc_meta["grant_id"] = grant_id

    if doc.attached_to_doctype == "Grant Project":
        project_id = doc.attached_to_name
        grant_id = frappe.get_value("Grant Project", project_id, fieldname="grant")

    if doc.attached_to_doctype == "Grant Project Milestone":
        milestone_id = doc.attached_to_name
        project_id = frappe.get_doc(
            "Grant Project Milestone", milestone_id, fieldname="project"
        )
        if not project_id:
            return
        grant_id = frappe.get_value("Grant Project", project_id, fieldname="grant")
        doc_meta["grant_id"] = grant_id
        doc_meta["project_id"] = project_id
        doc_meta["project_milestone_id"] = milestone_id

    # Assuming file_id always exist, it should be greater than 1
    if len(doc_meta) > 1:
        full_path = doc.get_full_path()
        buf = BytesIO(open(full_path, "rb").read())
        kb = KnowledgeBase(root_path=root_path)
        kb.ingest(buf, doc.file_name, doc_meta=doc_meta)


def remove_document_if_needed(doc: File):
    if (
        doc.file_type != "PDF"
        or doc.attached_to_name is None
        or doc.attached_to_doctype is None
    ):
        return
    remove_ingested_document(file_id=doc.name)


def remove_ingested_document(file_id: str):
    doc = frappe.get_doc("File", file_id)
    kb = KnowledgeBase()
    kb.remove(f'file_id = "{doc.name}"')
    print(f"Remove doc with file id {doc.name}")
