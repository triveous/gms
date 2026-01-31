"""
LangGraph to Vercel AI SDK UIMessage Converter.

This module provides conversion utilities between LangGraph stream output
and Vercel AI SDK UIMessage format.
"""

import json
import uuid
from typing import Any, Generator, TypedDict, Sequence

from langchain_core.messages import (
    AIMessage,
    AIMessageChunk,
    HumanMessage,
    SystemMessage,
    ToolMessage,
    BaseMessage,
)
from pydantic_ai.ui.vercel_ai.response_types import (
    BaseChunk,
    DataChunk,
    ErrorChunk,
    FileChunk,
    FinishChunk,
    ReasoningDeltaChunk,
    ReasoningEndChunk,
    ReasoningStartChunk,
    SourceDocumentChunk,
    SourceUrlChunk,
    StartChunk,
    TextDeltaChunk,
    TextEndChunk,
    TextStartChunk,
    ToolInputAvailableChunk,
    ToolInputDeltaChunk,
    ToolInputStartChunk,
    ToolOutputAvailableChunk,
    ToolOutputErrorChunk,
    DoneChunk,
    StartStepChunk,
    FinishStepChunk,
)

from .types import (
    DataPartState,
    FilePartState,
    ReasoningPartState,
    SourceDocumentPartState,
    SourceUrlPartState,
    TextPartState,
    ToolPartState,
    UIMessageState,
)


class UIMessagePart(TypedDict, total=False):
    """A part of a UIMessage."""

    type: str
    text: str
    state: str
    toolCallId: str
    input: Any
    output: Any
    errorText: str
    sourceId: str
    url: str
    title: str
    mediaType: str
    filename: str
    id: str
    data: Any
    providerMetadata: dict[str, Any]


class UIMessage(TypedDict, total=False):
    """Vercel AI SDK UIMessage format."""

    id: str
    role: str
    metadata: dict[str, Any]
    parts: list[UIMessagePart]


class LangGraphUIMessageConverter:
    """
    Converts LangGraph stream output to Vercel AI SDK UIMessage format.

    This converter handles:
    - Text streaming (AIMessageChunk with text content)
    - Reasoning streaming (AIMessageChunk with reasoning content)
    - Tool call streaming (AIMessageChunk with tool_call_chunks)
    - Tool outputs (ToolMessage)
    - Custom data (stream_mode="custom")

    Example usage:
        converter = LangGraphUIMessageConverter()

        for event in agent.stream(state, config, stream_mode=["messages", "custom"]):
            namespace, stream_mode, data = event
            for chunk in converter.convert_stream_event(stream_mode, data):
                yield chunk.encode()

        # Get final UIMessage
        ui_message = converter.to_ui_message()
    """

    def __init__(self, message_id: str | None = None):
        """
        Initialize the converter.

        Args:
            message_id: Optional ID for the UIMessage. If not provided, a UUID will be generated.
        """
        self.message_id = message_id or str(uuid.uuid4())
        self.state = UIMessageState(id=self.message_id)
        self._started = False
        self._finished = False

        # Track which parts have been started/ended for streaming
        self._active_text_ids: set[str] = set()
        self._active_reasoning_ids: set[str] = set()
        self._active_tool_ids: set[str] = set()

    def _generate_part_id(self, prefix: str = "part") -> str:
        """Generate a unique ID for a message part."""
        return f"{prefix}-{uuid.uuid4().hex[:8]}"

    def start(self) -> list[BaseChunk]:
        """
        Generate start chunks for the stream.

        Returns:
            List containing StartChunk.
        """
        if self._started:
            return []

        self._started = True
        return [StartChunk(message_id=self.message_id)]

    def finish(self) -> list[BaseChunk]:
        """
        Generate finish chunks for the stream.

        This will close any open text/reasoning parts and emit finish/done chunks.

        Returns:
            List containing end chunks for active parts, FinishChunk, and DoneChunk.
        """
        if self._finished:
            return []

        self._finished = True
        chunks: list[BaseChunk] = []

        # Close any active text parts
        for text_id in list(self._active_text_ids):
            self.state.text_parts[text_id].state = "done"
            chunks.append(TextEndChunk(id=text_id))
            self._active_text_ids.discard(text_id)

        # Close any active reasoning parts
        for reasoning_id in list(self._active_reasoning_ids):
            self.state.reasoning_parts[reasoning_id].state = "done"
            chunks.append(ReasoningEndChunk(id=reasoning_id))
            self._active_reasoning_ids.discard(reasoning_id)

        chunks.append(FinishChunk(finish_reason="stop"))
        chunks.append(DoneChunk())

        return chunks

    def convert_stream_event(
        self, stream_mode: str, data: Any
    ) -> Generator[BaseChunk, None, None]:
        """
        Convert a LangGraph stream event to Vercel AI chunks.

        Args:
            stream_mode: The stream mode ("messages" or "custom")
            data: The stream data

        Yields:
            BaseChunk objects for the Vercel AI SSE stream.
        """
        if stream_mode == "messages":
            yield from self._convert_messages_event(data)
        elif stream_mode == "custom":
            yield from self._convert_custom_event(data)

    def _convert_messages_event(self, data: Any) -> Generator[BaseChunk, None, None]:
        """Convert a 'messages' stream event."""
        if not isinstance(data, tuple) or len(data) < 2:
            return

        message, metadata = data[0], data[1] if len(data) > 1 else {}

        if isinstance(message, AIMessageChunk):
            yield from self._convert_ai_message_chunk(message)
        elif isinstance(message, ToolMessage):
            yield from self._convert_tool_message(message)

    def _convert_ai_message_chunk(
        self, chunk: AIMessageChunk
    ) -> Generator[BaseChunk, None, None]:
        """
        Convert an AIMessageChunk to Vercel AI chunks.

        Handles:
        - Text content blocks
        - Reasoning content blocks
        - Tool call chunks
        """
        # Get content blocks from the chunk
        content_blocks = chunk.content_blocks

        for block in content_blocks:
            block_type = block.get("type")

            if block_type == "text":
                yield from self._handle_text_block(chunk.id or self.message_id, block)

            elif block_type == "reasoning":
                yield from self._handle_reasoning_block(
                    chunk.id or self.message_id, block
                )

            elif block_type == "tool_call_chunk":
                yield from self._handle_tool_call_chunk(block)

            elif block_type == "tool_call":
                yield from self._handle_tool_call_complete(block)

    def _handle_text_block(
        self, message_id: str, block: dict[str, Any]
    ) -> Generator[BaseChunk, None, None]:
        """Handle a text content block."""
        text = block.get("text", "")
        text_id = block.get("id") or message_id

        if text_id not in self.state.text_parts:
            # New text part - emit start
            self.state.text_parts[text_id] = TextPartState(id=text_id)
            self._active_text_ids.add(text_id)
            yield TextStartChunk(id=text_id)

        if text:
            # Emit delta
            self.state.text_parts[text_id].text += text
            yield TextDeltaChunk(id=text_id, delta=text)

    def _handle_reasoning_block(
        self, message_id: str, block: dict[str, Any]
    ) -> Generator[BaseChunk, None, None]:
        """Handle a reasoning content block."""
        text = block.get("reasoning", "") or block.get("text", "")
        reasoning_id = block.get("id") or f"reasoning-{message_id}"
        provider_metadata = block.get("provider_metadata")

        if reasoning_id not in self.state.reasoning_parts:
            # New reasoning part - emit start
            self.state.reasoning_parts[reasoning_id] = ReasoningPartState(
                id=reasoning_id, provider_metadata=provider_metadata
            )
            self._active_reasoning_ids.add(reasoning_id)
            yield ReasoningStartChunk(
                id=reasoning_id, provider_metadata=provider_metadata
            )

        if text:
            # Emit delta
            self.state.reasoning_parts[reasoning_id].text += text
            yield ReasoningDeltaChunk(
                id=reasoning_id, delta=text, provider_metadata=provider_metadata
            )

    def _handle_tool_call_chunk(
        self, block: dict[str, Any]
    ) -> Generator[BaseChunk, None, None]:
        """Handle a streaming tool call chunk."""
        tool_call_id = block.get("id") or self._generate_part_id("tool")
        tool_name = block.get("name") or ""
        args_str = block.get("args") or ""

        if tool_call_id not in self.state.tool_parts:
            # New tool call - emit start
            self.state.tool_parts[tool_call_id] = ToolPartState(
                tool_call_id=tool_call_id, tool_name=tool_name or "unknown"
            )
            self._active_tool_ids.add(tool_call_id)
            yield ToolInputStartChunk(
                tool_call_id=tool_call_id, tool_name=tool_name or "unknown"
            )

        # Update tool name if provided
        if tool_name and not self.state.tool_parts[tool_call_id].tool_name:
            self.state.tool_parts[tool_call_id].tool_name = tool_name

        if args_str:
            # Emit input delta
            self.state.tool_parts[tool_call_id].input_json += args_str
            yield ToolInputDeltaChunk(
                tool_call_id=tool_call_id, input_text_delta=args_str
            )

    def _handle_tool_call_complete(
        self, block: dict[str, Any]
    ) -> Generator[BaseChunk, None, None]:
        """Handle a complete tool call."""
        tool_call_id = block.get("id") or self._generate_part_id("tool")
        tool_name = block.get("name") or "unknown"
        args = block.get("args", {})

        if tool_call_id not in self.state.tool_parts:
            # New complete tool call (not streamed)
            self.state.tool_parts[tool_call_id] = ToolPartState(
                tool_call_id=tool_call_id,
                tool_name=tool_name,
                input=args,
                state="input-available",
            )
        else:
            # Update existing
            self.state.tool_parts[tool_call_id].input = args
            self.state.tool_parts[tool_call_id].state = "input-available"

        self._active_tool_ids.discard(tool_call_id)

        yield ToolInputAvailableChunk(
            tool_call_id=tool_call_id, tool_name=tool_name, input=args
        )

    def _convert_tool_message(
        self, message: ToolMessage
    ) -> Generator[BaseChunk, None, None]:
        """Convert a ToolMessage (tool output) to Vercel AI chunks."""
        tool_call_id = message.tool_call_id

        if tool_call_id in self.state.tool_parts:
            tool_state = self.state.tool_parts[tool_call_id]

            # Check if this is an error
            if hasattr(message, "status") and message.status == "error":
                tool_state.state = "output-error"
                tool_state.error_text = str(message.content)
                yield ToolOutputErrorChunk(
                    tool_call_id=tool_call_id, error_text=str(message.content)
                )
            else:
                tool_state.state = "output-available"
                tool_state.output = message.content
                yield ToolOutputAvailableChunk(
                    tool_call_id=tool_call_id, output=message.content
                )

    def _convert_custom_event(self, data: Any) -> Generator[BaseChunk, None, None]:
        """Convert a 'custom' stream event (data chunks)."""
        if isinstance(data, BaseChunk):
            # Already a Vercel chunk, pass through
            yield data
        elif isinstance(data, dict):
            # Convert dict to DataChunk
            data_type = data.get("type", "data-custom")
            if not data_type.startswith("data-"):
                data_type = f"data-{data_type}"

            data_id = data.get("id")
            data_content = data.get("data", data)
            transient = data.get("transient", False)

            self.state.data_parts.append(
                DataPartState(
                    type=data_type, id=data_id, data=data_content, transient=transient
                )
            )

            yield DataChunk(
                type=data_type, id=data_id, data=data_content, transient=transient
            )

    def to_ui_message(self) -> UIMessage:
        """
        Build a final UIMessage from accumulated state.

        Returns:
            UIMessage dict representing the complete message.
        """
        parts: list[UIMessagePart] = []

        # Add text parts
        for text_state in self.state.text_parts.values():
            parts.append(
                {"type": "text", "text": text_state.text, "state": text_state.state}
            )

        # Add reasoning parts
        for reasoning_state in self.state.reasoning_parts.values():
            part: UIMessagePart = {
                "type": "reasoning",
                "text": reasoning_state.text,
                "state": reasoning_state.state,
            }
            if reasoning_state.provider_metadata:
                part["providerMetadata"] = reasoning_state.provider_metadata
            parts.append(part)

        # Add tool parts
        for tool_state in self.state.tool_parts.values():
            part: UIMessagePart = {
                "type": f"tool-{tool_state.tool_name}",
                "toolCallId": tool_state.tool_call_id,
                "state": tool_state.state,
            }
            if tool_state.input is not None:
                part["input"] = tool_state.input
            if tool_state.output is not None:
                part["output"] = tool_state.output
            if tool_state.error_text:
                part["errorText"] = tool_state.error_text
            parts.append(part)

        # Add source URL parts
        for source_state in self.state.source_url_parts.values():
            part: UIMessagePart = {
                "type": "source-url",
                "sourceId": source_state.source_id,
                "url": source_state.url,
            }
            if source_state.title:
                part["title"] = source_state.title
            if source_state.provider_metadata:
                part["providerMetadata"] = source_state.provider_metadata
            parts.append(part)

        # Add source document parts
        for source_state in self.state.source_document_parts.values():
            part: UIMessagePart = {
                "type": "source-document",
                "sourceId": source_state.source_id,
                "mediaType": source_state.media_type,
                "title": source_state.title,
            }
            if source_state.filename:
                part["filename"] = source_state.filename
            if source_state.provider_metadata:
                part["providerMetadata"] = source_state.provider_metadata
            parts.append(part)

        # Add file parts
        for file_state in self.state.file_parts:
            part: UIMessagePart = {
                "type": "file",
                "mediaType": file_state.media_type,
                "url": file_state.url,
            }
            if file_state.filename:
                part["filename"] = file_state.filename
            parts.append(part)

        # Add data parts (non-transient only)
        for data_state in self.state.data_parts:
            if not data_state.transient:
                part: UIMessagePart = {"type": data_state.type, "data": data_state.data}
                if data_state.id:
                    part["id"] = data_state.id
                parts.append(part)

        return UIMessage(
            id=self.state.id,
            role=self.state.role,
            metadata=self.state.metadata,
            parts=parts,
        )

    def encode_error(self, error_text: str) -> BaseChunk:
        """
        Create an error chunk.

        Args:
            error_text: The error message.

        Returns:
            ErrorChunk for the SSE stream.
        """
        return ErrorChunk(error_text=error_text)


# Key used to store UI data parts in message additional_kwargs
UI_DATA_PARTS_KEY = "ui_data_parts"


def get_ui_data_parts(message: BaseMessage) -> list[dict]:
    """
    Get persisted UI data parts from a message's additional_kwargs.

    Reads from UI_DATA_PARTS_KEY in additional_kwargs and returns
    a flat list of data parts.

    Args:
        message: The message to read data from

    Returns:
        List of data part dicts, or empty list if none.
    """
    data_dict = message.additional_kwargs.get(UI_DATA_PARTS_KEY)
    if not data_dict:
        return []

    # Handle flat format: {"data_parts": [list of dicts with type field]}
    data_parts = data_dict.get("data_parts", [])
    if data_parts:
        return data_parts

    # Handle legacy categorized format
    parts = []
    for key in ["source_urls", "source_documents", "files"]:
        parts.extend(data_dict.get(key, []))
    return parts


def convert_message_to_ui_message(
    message: BaseMessage,
    tool_outputs: dict[str, Any] | None = None,
) -> UIMessage:
    """
    Convert a single LangGraph message to UIMessage format.

    Args:
        message: A LangGraph message (HumanMessage, AIMessage, SystemMessage, ToolMessage)
        tool_outputs: Optional dict mapping tool_call_id to output for completed tool calls

    Returns:
        UIMessage dict representing the message.
    """
    message_id = message.id or str(uuid.uuid4())
    tool_outputs = tool_outputs or {}

    # Determine role
    if isinstance(message, HumanMessage):
        role = "user"
    elif isinstance(message, SystemMessage):
        role = "system"
    elif isinstance(message, (AIMessage, AIMessageChunk)):
        role = "assistant"
    elif isinstance(message, ToolMessage):
        # ToolMessage is typically part of assistant context, not standalone
        role = "assistant"
    else:
        role = "assistant"

    parts: list[UIMessagePart] = []

    # Handle different message types
    if isinstance(message, (AIMessage, AIMessageChunk)):
        content_blocks = message.content_blocks

        for block in content_blocks:
            block_type = block.get("type")

            if block_type == "text":
                text = block.get("text", "")
                if text:
                    parts.append({"type": "text", "text": text, "state": "done"})

            elif block_type == "reasoning":
                text = block.get("reasoning", "") or block.get("text", "")
                if text:
                    part: UIMessagePart = {
                        "type": "reasoning",
                        "text": text,
                        "state": "done",
                    }
                    if provider_metadata := block.get("provider_metadata"):
                        part["providerMetadata"] = provider_metadata
                    parts.append(part)

            elif block_type == "tool_call":
                tool_call_id = block.get("id", "")
                tool_name = block.get("name", "unknown")
                args = block.get("args", {})

                # Check if we have output for this tool call
                output = tool_outputs.get(tool_call_id)

                part: UIMessagePart = {
                    "type": f"tool-{tool_name}",
                    "toolCallId": tool_call_id,
                    "input": args,
                    "state": "output-available"
                    if output is not None
                    else "input-available",
                }
                if output is not None:
                    part["output"] = output
                parts.append(part)

        # Also check tool_calls attribute on AIMessage
        if hasattr(message, "tool_calls") and message.tool_calls:
            for tc in message.tool_calls:
                tool_call_id = tc.get("id", "")
                # Skip if already processed from content_blocks
                if any(p.get("toolCallId") == tool_call_id for p in parts):
                    continue

                tool_name = tc.get("name", "unknown")
                args = tc.get("args", {})
                output = tool_outputs.get(tool_call_id)

                part: UIMessagePart = {
                    "type": f"tool-{tool_name}",
                    "toolCallId": tool_call_id,
                    "input": args,
                    "state": "output-available"
                    if output is not None
                    else "input-available",
                }
                if output is not None:
                    part["output"] = output
                parts.append(part)

    elif isinstance(message, (HumanMessage, SystemMessage)):
        # Simple text content
        content = message.content
        if isinstance(content, str):
            if content:
                parts.append({"type": "text", "text": content, "state": "done"})
        elif isinstance(content, list):
            # Handle multimodal content
            for item in content:
                if isinstance(item, str):
                    if item:
                        parts.append({"type": "text", "text": item, "state": "done"})
                elif isinstance(item, dict):
                    item_type = item.get("type")
                    if item_type == "text":
                        text = item.get("text", "")
                        if text:
                            parts.append(
                                {"type": "text", "text": text, "state": "done"}
                            )
                    elif item_type == "image_url":
                        url = item.get("image_url", {}).get("url", "")
                        if url:
                            parts.append(
                                {"type": "file", "mediaType": "image/*", "url": url}
                            )

    # Read persisted UI data parts from additional_kwargs
    ui_data_parts = get_ui_data_parts(message)
    if ui_data_parts:
        parts.extend(ui_data_parts)

    return UIMessage(id=message_id, role=role, parts=parts)


def convert_messages_to_ui_messages(
    messages: Sequence[BaseMessage],
) -> list[UIMessage]:
    """
    Convert a list of LangGraph messages to UIMessage format for chat history display.

    This function processes a complete message history and converts each message
    to the Vercel AI SDK UIMessage format. It automatically pairs ToolMessages
    with their corresponding AIMessage tool calls.

    Args:
        messages: List of LangGraph messages (HumanMessage, AIMessage, SystemMessage, ToolMessage)

    Returns:
        List of UIMessage dicts representing the chat history.

    Example:
        from langchain_core.messages import HumanMessage, AIMessage
        from gms.ai.agents_v2.vercel_ui import convert_messages_to_ui_messages

        # Get messages from agent state or checkpoint
        messages = agent.get_state(config).values.get("messages", [])

        # Convert to UIMessage format
        ui_messages = convert_messages_to_ui_messages(messages)

        # Return to frontend
        return ui_messages
    """
    ui_messages: list[UIMessage] = []

    # First pass: collect tool outputs from ToolMessages
    tool_outputs: dict[str, Any] = {}
    for msg in messages:
        if isinstance(msg, ToolMessage):
            tool_outputs[msg.tool_call_id] = msg.content

    # Second pass: convert messages (skip ToolMessages as they're merged into AIMessage)
    for msg in messages:
        if isinstance(msg, ToolMessage):
            # Tool outputs are already paired with their AIMessage tool calls
            continue

        ui_message = convert_message_to_ui_message(msg, tool_outputs)

        # Only add if message has parts
        if ui_message.get("parts"):
            ui_messages.append(ui_message)

    return ui_messages
