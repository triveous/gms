from io import BytesIO

import frappe
from frappe.utils import now
from gms.ai.agents.base.knowledge_base import KnowledgeBase
from gms.ai.doctype.ai_document.ai_document import AIDocument


def after_insert(doc: AIDocument, method):
    frappe.enqueue(
        "gms.api.ai_document.index_ai_document",
        ai_document_id=doc.name,
        forced=False,
        queue="long",
        job_id=doc.name,
        at_front=True,
    )
    frappe.log(f"Queueed ai document indexing for {doc.name}")


def after_delete(doc: AIDocument, method):
    frappe.enqueue(
        "gms.api.ai_document.remove_from_index",
        ai_document_id=doc.name,
        file_id=doc.file,
        queue="long",
        job_id=doc.name,
        at_front=True,
    )
    frappe.log(f"Queueed ai document unindexing for {doc.name}")


@frappe.whitelist()
def retry_indexing():
    ai_document_id = frappe.form_dict.get("ai_document_id")
    ai_document = frappe.get_doc("AI Document", ai_document_id)
    if ai_document.processing_status == "Success":
        frappe.log("Document already processed")
        return

    # Enqueue indexing
    frappe.enqueue(
        "gms.api.ai_document.index_ai_document",
        ai_document_id=ai_document_id,
        queue="long",
        job_id=ai_document,
        forced=True,
        at_front=True,
    )


def index_ai_document(ai_document_id: str, forced: bool):
    """
    Index the AI Document into the Knowledgebase and udpate the indexing status
    """

    ai_document = frappe.get_doc("AI Document", ai_document_id)
    if ai_document.processing_status == "Success":
        frappe.log("Document already processed")
        return

    if ai_document.processing_attempts >= 20 and not forced:
        frappe.log("Max Retry Attempted")
        return

    file_id = ai_document.file
    file = frappe.get_doc("File", ai_document.file)

    def process():
        doc_meta = {"file_id": file_id, "ai_document_id": ai_document_id}
        root_path = "Home/IndexedFiles"

        if file.file_type != "PDF":
            return False, "File Should be PDF Only"

        if file.attached_to_doctype == "Grant":
            grant_id = file.attached_to_name
            doc_meta["grant_id"] = grant_id

        if file.attached_to_doctype == "Grant Project":
            project_id = file.attached_to_name
            project = frappe.get_doc("Grant Project", project_id)
            grant_id = project.grant
            if not grant_id:
                return False

            doc_meta["grant_id"] = grant_id
            doc_meta["project_id"] = project_id

        if file.attached_to_doctype == "Grant Project Milestone":
            milestone_id = file.attached_to_name
            project_milestone = frappe.get_doc("Grant Project Milestone", milestone_id)
            project_id = project_milestone.project
            if not project_id:
                return False

            project = frappe.get_doc("Grant Project", project_id)
            grant_id = project.grant
            if not grant_id:
                return False
            doc_meta["grant_id"] = grant_id
            doc_meta["project_id"] = project_id
            doc_meta["project_milestone_id"] = milestone_id

        # Assuming file_id always exist, it should be greater than 1
        full_path = file.get_full_path()
        buf = BytesIO(open(full_path, "rb").read())
        kb = KnowledgeBase(root_path=root_path)
        kb.ingest(buf, file.file_name, doc_meta=doc_meta)
        frappe.log("Ingested")
        return True, None

    frappe.log(f"Processing File {file.name} from AI Document {ai_document_id}")
    try:
        ai_document.processing_attempts = ai_document.processing_attempts + 1
        ai_document.processing_last_attempted_at = now()
        processed, reason = process()

        if processed:
            ai_document.processing_status = "Success"
            frappe.log("Processed AI Document")
        else:
            # No reattemp will be done here
            ai_document.failure_reason = reason
            ai_document.processing_status = "Failed"
            error_log = frappe.log_error(
                f"AI Document Ingestion Failed - {ai_document}"
            )
            ai_document.error_log = error_log

    except Exception:
        error_log = frappe.log_error(f"AI Document Ingestion Failed - {ai_document}")
        ai_document.error_log = error_log
        ai_document.processing_status = "Failed"
        ai_document.failure_reason = "Execution Error"
    finally:
        # Save all the changes
        ai_document.save()
        frappe.db.commit()


def remove_from_index(ai_document_id: str, file_id: str):
    kb = KnowledgeBase()
    kb.remove(
        expr=f'ai_document_id == "{ai_document_id}" or file_id == "{file_id}"',
    )
    frappe.log("Unindexed")
