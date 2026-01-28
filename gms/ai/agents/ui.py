import asyncio
from typing import Any, AsyncIterator, Callable

from anyio import create_memory_object_stream
from anyio.streams.memory import MemoryObjectSendStream
from pydantic_ai.ui.vercel_ai import (
    VercelAIAdapter as BaseVercelAIAdapter,
)
from pydantic_ai.ui.vercel_ai.response_types import (
    BaseChunk,
)


class CustomUIEventSender:
    def __init__(self, send_stream: MemoryObjectSendStream):
        self.send_stream = send_stream

    async def send_event(self, event: BaseChunk):
        encoded = f"data: {event.encode()}\n\n"
        await self.send_stream.send(encoded)


class CustomUIEventAdapter:
    def __init__(self):
        self._send_stream, self._receive_stream = create_memory_object_stream(
            max_buffer_size=64
        )
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
        loop = asyncio.get_running_loop()
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


class VercelAIAdapterCustom(BaseVercelAIAdapter):
    @staticmethod
    def set_loop():
        """Ensure that there is a running event loop."""
        get_event_loop()

    def run_encoded_sync(
        self,
        dep_builder: Callable[[MemoryObjectSendStream], Any],
        message_history,
        on_complete=None,
        on_start=None,
    ):
        return stream_async_iterator(
            self.run_encoded(
                dep_builder=dep_builder,
                message_history=message_history,
                on_complete=on_complete,
                on_start=on_start,
            )
        )

    def run_encoded(
        self,
        dep_builder: Callable[[MemoryObjectSendStream], Any],
        message_history,
        on_complete,
        on_start,
    ):
        # This ensures that we have an event loop
        get_event_loop()

        send_stream, receive_stream = create_memory_object_stream()

        # Pipe the encoded stream to the send stream
        async def runner(deps):
            # Run the agent to generate UI Events
            ui_stream = self.run_stream(
                deps=deps,
                message_history=message_history,
                on_complete=lambda result: on_complete(deps, result),
            )

            # Encoded the UI stream to SSE format
            encoded_ui_stream = self.encode_stream(ui_stream)

            # Till the stream is open, forward the encoded events to send_stream
            # Other event which are to forwared to send_stream can be done in the tools using the same async await
            async with send_stream:
                async for event in encoded_ui_stream:
                    await send_stream.send(event)

        async def stream_generator() -> AsyncIterator[str]:
            # Build the deps
            deps = dep_builder(send_stream)

            # FIX: Use asyncio.create_task instead of create_task_group.
            # This schedules the runner on the loop without binding it
            # to the specific Task ID of the first chunk's execution.
            runner_task = asyncio.create_task(runner(deps))
            on_start_task = asyncio.create_task(on_start(deps)) if on_start else None

            try:
                async with receive_stream:
                    async for event in receive_stream:
                        yield event
            except Exception as e:
                print(e)
                # If the WSGI client disconnects or an error occurs reading,
                # cancel the runner to prevent orphaned tasks.
                runner_task.cancel()
                if on_start_task:
                    on_start_task.cancel()

                raise

            # Optional: Await the runner to propagate any exceptions that happened inside it
            # If the stream finished normally, this will return immediately.
            try:
                await runner_task
                if on_start_task:
                    await on_start_task
            except Exception as e:
                print(e)
                raise

        return stream_generator()
