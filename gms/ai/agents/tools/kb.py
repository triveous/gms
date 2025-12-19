from gms.ai.agents.base.knowledge_base import kb

def read_kb(query: str):
    """Search the knowledgebase.
    Args:
        query: str The query to search for.
    """
    return kb.retrieve(query)
