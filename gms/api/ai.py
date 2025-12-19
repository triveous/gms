
from gms.ai.agents.base.knowledge_base import kb
from aikam.apps.gms.gms.ai.agents.chat_agent import aikam_agent

import frappe

@frappe.whitelist(allow_guest=True)
def ingest_to_kb():
    # result = kb.retrieve("Can you tell me what is AICOE")
    try:
        kb.ingest(src="/workspace/development/docs/AICOE_SUS_CITIES.pdf", name="AICOE_SUSTAINABLE_CITIES.pdf")
    except Exception as e:
        print(e)
        return "Failed"
    # frappe.enqueue(do_ingest_to_kb, queue='long')
    return result
