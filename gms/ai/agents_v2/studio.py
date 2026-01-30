# This studio code is meant to be used on development setup and not absolutely no production setup
# So we don't have all the deps automatically installed to run this code. You will need to run
#       `bench pip langgraph-cli[inmem]`
# To start the studio server. you need to be have langgraph.json file in the sites folder and start the studio
# by calling `langgraph dev`
# Additional install debugpy to enable debugging


### Content of langgraph.json
# {
#   "dependencies": [
#     "."
#   ],
#   "graphs": {
#     "chat": "./gms/ai/agents_v2/studio.py:agent"
#   },
#   "env": ".env"
# }
###
import frappe


# Intialize Frappe
def intialize_frappe():
    SITE = "d.localhost"
    frappe.init(SITE, sites_path=".")
    frappe.connect()
    print("Frappe connected")


intialize_frappe()


settings = frappe.get_single("AI Settings")
kb_connection_uri = settings.milvus_db_url
kb_token = settings.milvus_db_token

from gms.ai.agents_v2.agents.chat_agent import create_chat_agent  # noqa: E402
from gms.ai.kb.kb import Knowledge  # noqa: E402

knowledgebase = Knowledge(uri=kb_connection_uri, token=kb_token)
agent = create_chat_agent(knowledge=knowledgebase)
