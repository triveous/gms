from typing import AsyncIterator, Callable
import asyncio

from anyio import create_memory_object_stream
from anyio.streams.memory import MemoryObjectSendStream
from pydantic_ai.ui.vercel_ai.response_types import BaseChunk


class CustomUIEventSender:
    def __init__(self, send_stream: MemoryObjectSendStream):
        self.send_stream = send_stream

    async def send_event(self, event: BaseChunk):
        encoded = f"data: {event.encode()}\n\n"
        await self.send_stream.send(encoded)


class CustomUIEventAdapter:
    def __init__(self):
        self._send_stream, self._receive_stream = create_memory_object_stream()
        self._sender = CustomUIEventSender(self._send_stream)
        self._forward_task: asyncio.Task | None = None

    def get_sender(self):
        return self._sender

    async def _forward(self, event_stream: AsyncIterator[str]):
        try:
            async with self._send_stream:
                async for event in event_stream:
                    await self._send_stream.send(event)
        finally:
            await self._send_stream.aclose()

    async def _stream(self, event_stream: AsyncIterator[str]):
        loop = asyncio.get_running_loop()

        # Start background forwarder ONCE
        self._forward_task = loop.create_task(self._forward(event_stream))

        async with self._receive_stream:
            async for event in self._receive_stream:
                yield event

        await self._forward_task

    def run(
        self,
        default_ui_event_stream: AsyncIterator,
        encoder: Callable[[AsyncIterator], AsyncIterator[str]],
    ) -> AsyncIterator[str]:
        encoded = encoder(default_ui_event_stream)
        return self._stream(encoded)

    def run_sync(self, ui_event_stream, encoder):
        return stream_async_iterator(self.run(ui_event_stream, encoder))


def get_event_loop():
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            raise RuntimeError
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop


def stream_async_iterator(async_iter: AsyncIterator[str]):
    """AsyncIterator → sync generator (Werkzeug-safe)."""
    loop = get_event_loop()

    try:
        while True:
            yield loop.run_until_complete(anext(async_iter))
    except StopAsyncIteration:
        return