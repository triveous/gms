"""
Vercel UI SDK types for LangGraph stream conversion.

This module defines the internal state tracking types used by the converter.
"""

from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass
class TextPartState:
    """State for tracking a text part during streaming."""

    id: str
    text: str = ""
    state: Literal["streaming", "done"] = "streaming"


@dataclass
class ReasoningPartState:
    """State for tracking a reasoning part during streaming."""

    id: str
    text: str = ""
    state: Literal["streaming", "done"] = "streaming"
    provider_metadata: dict[str, Any] | None = None


@dataclass
class ToolPartState:
    """State for tracking a tool call part during streaming."""

    tool_call_id: str
    tool_name: str
    input_json: str = ""
    input: dict[str, Any] | None = None
    output: Any = None
    error_text: str | None = None
    provider_executed: bool = False
    state: Literal[
        "input-streaming", "input-available", "output-available", "output-error"
    ] = "input-streaming"


@dataclass
class SourceUrlPartState:
    """State for tracking a source URL part."""

    source_id: str
    url: str
    title: str | None = None
    provider_metadata: dict[str, Any] | None = None


@dataclass
class SourceDocumentPartState:
    """State for tracking a source document part."""

    source_id: str
    media_type: str
    title: str
    filename: str | None = None
    provider_metadata: dict[str, Any] | None = None


@dataclass
class FilePartState:
    """State for tracking a file part."""

    url: str
    media_type: str
    filename: str | None = None


@dataclass
class DataPartState:
    """State for tracking a custom data part."""

    type: str  # Should be "data-{name}"
    id: str | None = None
    data: Any = None
    transient: bool = False


@dataclass
class UIMessageState:
    """Complete state for a UIMessage being built from stream."""

    id: str
    role: Literal["system", "user", "assistant"] = "assistant"
    metadata: dict[str, Any] = field(default_factory=dict)

    # Part states
    text_parts: dict[str, TextPartState] = field(default_factory=dict)
    reasoning_parts: dict[str, ReasoningPartState] = field(default_factory=dict)
    tool_parts: dict[str, ToolPartState] = field(default_factory=dict)
    source_url_parts: dict[str, SourceUrlPartState] = field(default_factory=dict)
    source_document_parts: dict[str, SourceDocumentPartState] = field(
        default_factory=dict
    )
    file_parts: list[FilePartState] = field(default_factory=list)
    data_parts: list[DataPartState] = field(default_factory=list)
    step_boundaries: list[int] = field(
        default_factory=list
    )  # Indices where steps start
