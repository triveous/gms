from pydantic_ai.ui.vercel_ai import VercelAIAdapter
from pydantic_ai.ui import SSE_CONTENT_TYPE
from pydantic import ValidationError
from gms.ai.agents.aikam import aikam_agent
from gms.utils.iterator import stream_async_iterator
from werkzeug.wrappers import Response

import frappe
import json


@frappe.whitelist(allow_guest=True)
def run():
    accept = frappe.request.headers.get("accept", SSE_CONTENT_TYPE)
     # Access JSON data sent in the request body
    if frappe.request.data:
        try:
            run_input = VercelAIAdapter.build_run_input(frappe.request.data)
        except ValidationError as e:
            return "Failed"
        
        adapter = VercelAIAdapter(agent=aikam_agent, run_input=run_input, accept=accept)
        # Conver to UIMessageData Protocol
        event_stream = adapter.run_stream()
        # Serialized the message to string which text stream
        sse_event_stream = adapter.encode_stream(event_stream)
        
        return Response(
            stream_async_iterator(sse_event_stream),
            status=200,
            headers={
                "Content-Type": "text/event-stream",
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Stream-Type": "limited",
            },
        )
    return "No data received in the body"
