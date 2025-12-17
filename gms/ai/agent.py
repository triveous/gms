from pydantic_ai import Agent
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.ui.vercel_ai import VercelAIAdapter
from pydantic_ai.ui import SSE_CONTENT_TYPE
from pydantic import ValidationError

from werkzeug.wrappers import Response

import frappe
import json

aikam_agent = Agent(
    GoogleModel("gemini-2.5-flash",provider=GoogleProvider(api_key="API_KEY")),
    system_prompt=f"""Your are helpful assistant"""
)


@frappe.whitelist(allow_guest=True)
def chat():
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

def get_event_loop():
    import asyncio
    try:
        event_loop = asyncio.get_event_loop()
    except RuntimeError:  # pragma: lax no cover
        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)
    return event_loop


def stream_async_iterator(async_iter):
    """Bridge for AsyncIterator to Synchronous Generator."""
    loop = get_event_loop()
    while True:
        try:
            # Drive the async iterator inside a one-off loop run
            yield loop.run_until_complete(anext(async_iter))
        except StopAsyncIteration:
            break
            