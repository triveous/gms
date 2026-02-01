"""
Stream handlers for LangGraph to Vercel AI SDK conversion.

This module provides sync and async stream handlers that wrap the converter
for easy integration with LangGraph agents.
"""

import queue
import asyncio
from typing import Any, AsyncIterator, Iterator, Generator

from pydantic_ai.ui.vercel_ai.response_types import BaseChunk

from .converter import LangGraphUIMessageConverter, UIMessage


class VercelUIStreamHandler:
    """
    Synchronous stream handler for LangGraph to Vercel AI SSE format.

    This handler wraps the LangGraphUIMessageConverter and provides a simple
    interface for processing LangGraph stream events and yielding SSE chunks.

    Example usage:
        handler = VercelUIStreamHandler()

        for chunk in handler.start():
            yield chunk

        for stream_mode, data in agent.stream(state, config, stream_mode=["messages", "custom"]):
            for chunk in handler.process_event(stream_mode, data):
                yield chunk

        for chunk in handler.finish():
            yield chunk
    """

    def __init__(
        self,
        message_id: str | None = None,
        include_types: list[str] | None = None,
    ):
        """
        Initialize the stream handler.

        Args:
            message_id: Optional ID for the UIMessage. If not provided, a UUID will be generated.
            include_types: Optional list of types to include ("text", "reasoning", "tool", "data").
        """
        self.converter = LangGraphUIMessageConverter(
            message_id=message_id, include_types=include_types
        )
        self._queue: queue.Queue[str] = queue.Queue()

    @staticmethod
    def encode(chunk: BaseChunk) -> str:
        """Encode a chunk as an SSE data line."""
        return f"data: {chunk.encode()}\n\n"

    def start(self) -> Generator[str, None, None]:
        """
        Start the stream and yield start chunks as SSE.

        Yields:
            SSE-formatted start chunks.
        """
        for chunk in self.converter.start():
            yield self.encode(chunk)

    def process_event(self, stream_mode: str, data: Any) -> Generator[str, None, None]:
        """
        Process a LangGraph stream event and yield SSE chunks.

        Args:
            stream_mode: The stream mode ("messages" or "custom")
            data: The stream data

        Yields:
            SSE-formatted chunks.
        """
        for chunk in self.converter.convert_stream_event(stream_mode, data):
            yield self.encode(chunk)

    def finish(self) -> Generator[str, None, None]:
        """
        Finish the stream and yield finish chunks as SSE.

        Yields:
            SSE-formatted finish chunks.
        """
        for chunk in self.converter.finish():
            yield self.encode(chunk)

    def encode_error(self, error_text: str) -> str:
        """
        Create an SSE-formatted error.

        Args:
            error_text: The error message.

        Returns:
            SSE-formatted error chunk.
        """
        return self.encode(self.converter.encode_error(error_text))

    def to_ui_message(self) -> UIMessage:
        """
        Get the final UIMessage after stream completes.

        Returns:
            The complete UIMessage.
        """
        return self.converter.to_ui_message()

    @property
    def message_id(self) -> str:
        """Get the message ID."""
        return self.converter.message_id


class AsyncVercelUIStreamHandler:
    """
    Asynchronous stream handler for LangGraph to Vercel AI SSE format.

    This handler wraps the LangGraphUIMessageConverter and provides an async
    interface for processing LangGraph stream events and yielding SSE chunks.

    Example usage:
        handler = AsyncVercelUIStreamHandler()

        async for chunk in handler.start():
            yield chunk

        async for stream_mode, data in agent.astream(state, config, stream_mode=["messages", "custom"]):
            async for chunk in handler.process_event(stream_mode, data):
                yield chunk

        async for chunk in handler.finish():
            yield chunk
    """

    def __init__(
        self,
        message_id: str | None = None,
        include_types: list[str] | None = None,
    ):
        """
        Initialize the async stream handler.

        Args:
            message_id: Optional ID for the UIMessage. If not provided, a UUID will be generated.
            include_types: Optional list of types to include ("text", "reasoning", "tool", "data").
        """
        self.converter = LangGraphUIMessageConverter(
            message_id=message_id, include_types=include_types
        )
        self._queue: asyncio.Queue[str] = asyncio.Queue()

    @staticmethod
    def encode(chunk: BaseChunk) -> str:
        """Encode a chunk as an SSE data line."""
        return f"data: {chunk.encode()}\n\n"

    async def start(self) -> AsyncIterator[str]:
        """
        Start the stream and yield start chunks as SSE.

        Yields:
            SSE-formatted start chunks.
        """
        for chunk in self.converter.start():
            yield self.encode(chunk)

    async def process_event(self, stream_mode: str, data: Any) -> AsyncIterator[str]:
        """
        Process a LangGraph stream event and yield SSE chunks.

        Args:
            stream_mode: The stream mode ("messages" or "custom")
            data: The stream data

        Yields:
            SSE-formatted chunks.
        """
        for chunk in self.converter.convert_stream_event(stream_mode, data):
            yield self.encode(chunk)

    async def finish(self) -> AsyncIterator[str]:
        """
        Finish the stream and yield finish chunks as SSE.

        Yields:
            SSE-formatted finish chunks.
        """
        for chunk in self.converter.finish():
            yield self.encode(chunk)

    def encode_error(self, error_text: str) -> str:
        """
        Create an SSE-formatted error.

        Args:
            error_text: The error message.

        Returns:
            SSE-formatted error chunk.
        """
        return self.encode(self.converter.encode_error(error_text))

    def to_ui_message(self) -> UIMessage:
        """
        Get the final UIMessage after stream completes.

        Returns:
            The complete UIMessage.
        """
        return self.converter.to_ui_message()

    @property
    def message_id(self) -> str:
        """Get the message ID."""
        return self.converter.message_id


def stream_langgraph_to_vercel(
    stream_iterator: Iterator[tuple],
    message_id: str | None = None,
    include_types: list[str] | None = None,
) -> Generator[str, None, UIMessage]:
    """
    Convenience function to convert a LangGraph stream to Vercel AI SSE format.

    This function handles the complete streaming flow including start/finish.

    Args:
        stream_iterator: Iterator yielding (stream_mode, data) or (namespace, stream_mode, data) tuples
        message_id: Optional message ID

    Yields:
        SSE-formatted chunks.

    Returns:
        The final UIMessage after stream completes.
    """
    handler = VercelUIStreamHandler(message_id=message_id, include_types=include_types)

    # Start
    for chunk in handler.start():
        yield chunk

    # Process events
    for event in stream_iterator:
        if len(event) == 3:
            namespace, stream_mode, data = event
        elif len(event) == 2:
            stream_mode, data = event
        else:
            continue

        for chunk in handler.process_event(stream_mode, data):
            yield chunk

    # Finish
    for chunk in handler.finish():
        yield chunk

    return handler.to_ui_message()


async def astream_langgraph_to_vercel(
    stream_iterator: AsyncIterator[tuple],
    message_id: str | None = None,
    include_types: list[str] | None = None,
) -> AsyncIterator[str]:
    """
    Async convenience function to convert a LangGraph stream to Vercel AI SSE format.

    This function handles the complete streaming flow including start/finish.

    Args:
        stream_iterator: Async iterator yielding (namespace, stream_mode, data) tuples
        message_id: Optional message ID

    Yields:
        SSE-formatted chunks.
    """
    handler = AsyncVercelUIStreamHandler(
        message_id=message_id, include_types=include_types
    )

    # Start
    async for chunk in handler.start():
        yield chunk

    # Process events
    async for event in stream_iterator:
        if len(event) == 3:
            namespace, stream_mode, data = event
        elif len(event) == 2:
            stream_mode, data = event
        else:
            continue

        async for chunk in handler.process_event(stream_mode, data):
            yield chunk

    # Finish
    async for chunk in handler.finish():
        yield chunk
