"""
Vercel UI SDK utilities for LangGraph stream conversion.

This module provides converters and stream handlers to transform LangGraph
stream output into Vercel AI SDK UIMessage format.

Example usage (sync):
    from gms.ai.agents_v2.vercel_ui import VercelUIStreamHandler

    handler = VercelUIStreamHandler()

    for chunk in handler.start():
        yield chunk

    for stream_mode, data in agent.stream(state, config, stream_mode=["messages", "custom"]):
        for chunk in handler.process_event(stream_mode, data):
            yield chunk

    for chunk in handler.finish():
        yield chunk

Example usage (async):
    from gms.ai.agents_v2.vercel_ui import AsyncVercelUIStreamHandler

    handler = AsyncVercelUIStreamHandler()

    async for chunk in handler.start():
        yield chunk

    async for stream_mode, data in agent.astream(state, config, stream_mode=["messages", "custom"]):
        async for chunk in handler.process_event(stream_mode, data):
            yield chunk

    async for chunk in handler.finish():
        yield chunk

Convenience functions:
    from gms.ai.agents_v2.vercel_ui import stream_langgraph_to_vercel

    for chunk in stream_langgraph_to_vercel(agent.stream(...)):
        yield chunk
"""

from .converter import (
    LangGraphUIMessageConverter,
    UIMessage,
    UIMessagePart,
    convert_messages_to_ui_messages,
    convert_message_to_ui_message,
    get_ui_data_parts,
    UI_DATA_PARTS_KEY,
)
from .stream_handler import (
    VercelUIStreamHandler,
    AsyncVercelUIStreamHandler,
    stream_langgraph_to_vercel,
    astream_langgraph_to_vercel,
)
from .types import (
    TextPartState,
    ReasoningPartState,
    ToolPartState,
    SourceUrlPartState,
    SourceDocumentPartState,
    FilePartState,
    DataPartState,
    UIMessageState,
)

__all__ = [
    # Converter
    "LangGraphUIMessageConverter",
    "UIMessage",
    "UIMessagePart",
    "convert_messages_to_ui_messages",
    "convert_message_to_ui_message",
    "get_ui_data_parts",
    "UI_DATA_PARTS_KEY",
    # Stream handlers
    "VercelUIStreamHandler",
    "AsyncVercelUIStreamHandler",
    "stream_langgraph_to_vercel",
    "astream_langgraph_to_vercel",
    # State types
    "TextPartState",
    "ReasoningPartState",
    "ToolPartState",
    "SourceUrlPartState",
    "SourceDocumentPartState",
    "FilePartState",
    "DataPartState",
    "UIMessageState",
]
