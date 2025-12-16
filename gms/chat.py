def setup_ai_chat_route():
    try:
        from frappe.api import API_URL_MAP
        from werkzeug.routing import Rule
        import frappe
        API_URL_MAP.add(Rule("/api/ai/chat", endpoint=chat))
        print("AI Chat Route Configured")
    except:
        pass

def dummy_event_stream():
    for i in range(1, 11):
        yield f"data: {i}\n\n"
    yield "event: done\ndata: ok\n\n"
    
def chat():
    from werkzeug.wrappers import Response
    return Response(
        dummy_event_stream(),
        status=200,
        headers={
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Stream-Type": "limited",
        },
    )