"""
UI Stream Writer utility for LangGraph agents.

Provides a wrapper around LangGraph's get_stream_writer that tracks
data for persistence in agent state.
"""

from typing import Any, Callable
from langgraph.config import get_stream_writer


def ui_data_reducer(existing: dict | None, new: dict | None) -> dict:
    """
    Custom reducer for ui_data field that merges dicts without overwriting.

    Keys are formatted as "type:id" to allow multiple items of same type.

    Args:
        existing: Current state value (may be None on first call)
        new: New value to merge in

    Returns:
        Merged dict
    """
    if existing is None:
        existing = {}
    if new is None:
        return existing

    # Deep merge - new values extend/update existing
    result = dict(existing)
    for key, value in new.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            # Merge nested dicts
            result[key] = {**result[key], **value}
        else:
            result[key] = value

    return result


def get_ui_stream_writer() -> "UIStreamWriter":
    """
    Get a UIStreamWriter instance with the internal stream writer pre-loaded.

    This is the recommended way to create a UIStreamWriter in tools/middleware,
    as it ensures the stream writer is ready to use immediately.

    Returns:
        UIStreamWriter instance with stream writer initialized.

    Example:
        from gms.ai.agents_v2.utils import get_ui_stream_writer

        def my_tool(query: str):
            writer = get_ui_stream_writer()
            writer.write({"type": "source-url", "url": "https://example.com"})
            return Command(update={"ui_data": writer.get_state_update()})
    """
    writer = UIStreamWriter()
    writer._ensure_writer()  # Pre-load the stream writer
    return writer


class UIStreamWriter:
    """
    A stream writer wrapper that both streams data and tracks it for state persistence.

    This allows you to stream UI updates in real-time while also building up
    state data that can be persisted with the message.

    Usage in a tool or middleware:
        from gms.ai.agents_v2.utils.ui_stream_writer import UIStreamWriter

        def my_tool(query: str):
            writer = UIStreamWriter()

            # Write source URL (persisted by default)
            writer.write({
                "type": "source-url",
                "id": "src-1",
                "url": "https://example.com",
                "title": "Example"
            })

            # Write transient progress (NOT persisted)
            writer.write({
                "type": "data-progress",
                "data": {"step": 1},
                "transient": True
            })

            # Get state update to return from tool
            return {"result": "...", "ui_data": writer.get_state_update()}

    Usage with Command:
        from langgraph.types import Command

        return Command(
            update={"ui_data": writer.get_state_update()},
            # ... other command params
        )
    """

    def __init__(self):
        """Initialize the UI stream writer."""
        self._stream_writer: Callable | None = None
        self._collected_data: dict[str, Any] = {}
        self._initialized = False

    def _ensure_writer(self) -> Callable:
        """Lazily get the stream writer."""
        if self._stream_writer is None:
            self._stream_writer = get_stream_writer()
        return self._stream_writer

    def write(
        self,
        data: dict[str, Any],
        *,
        stream: bool = True,
    ) -> None:
        """
        Write data to the stream and optionally collect for state.

        Args:
            data: The data to write. Should have a "type" key.
                  If "transient": True, data is streamed only, not persisted.
                  If "id" is provided, it's used in the state key.
            stream: Whether to stream the data (default True)
        """
        transient = data.get("transient", False)

        # Stream the data
        if stream:
            writer = self._ensure_writer()
            writer(data)

        # Collect non-transient data for state
        if not transient:
            data_type = data.get("type", "data")
            data_id = data.get("id", data.get("sourceId", ""))

            # Create a unique key: "type:id" or just "type:index"
            if data_id:
                key = f"{data_type}:{data_id}"
            else:
                # Use incremental index for items without ID
                existing_count = sum(
                    1 for k in self._collected_data if k.startswith(f"{data_type}:")
                )
                key = f"{data_type}:{existing_count}"

            # Store the data (excluding transient flag)
            stored_data = {k: v for k, v in data.items() if k != "transient"}
            self._collected_data[key] = stored_data

    def write_source_url(
        self,
        source_id: str,
        url: str,
        title: str | None = None,
        *,
        transient: bool = False,
    ) -> None:
        """Convenience method to write a source URL."""
        data: dict[str, Any] = {
            "type": "source-url",
            "sourceId": source_id,
            "url": url,
        }
        if title:
            data["title"] = title
        if transient:
            data["transient"] = True
        self.write(data)

    def write_source_document(
        self,
        source_id: str,
        title: str,
        media_type: str = "text/plain",
        filename: str | None = None,
        *,
        transient: bool = False,
    ) -> None:
        """Convenience method to write a source document."""
        data: dict[str, Any] = {
            "type": "source-document",
            "sourceId": source_id,
            "title": title,
            "mediaType": media_type,
        }
        if filename:
            data["filename"] = filename
        if transient:
            data["transient"] = True
        self.write(data)

    def write_data(
        self,
        data_type: str,
        payload: Any,
        data_id: str | None = None,
        *,
        transient: bool = False,
    ) -> None:
        """
        Convenience method to write custom data.

        Args:
            data_type: Type name (will be prefixed with "data-" if needed)
            payload: The data payload
            data_id: Optional ID for the data
            transient: If True, stream only, don't persist
        """
        if not data_type.startswith("data-"):
            data_type = f"data-{data_type}"

        data: dict[str, Any] = {
            "type": data_type,
            "data": payload,
        }
        if data_id:
            data["id"] = data_id
        if transient:
            data["transient"] = True
        self.write(data)

    def get_state_update(self) -> dict[str, Any]:
        """
        Get the collected data as a state update dict.

        Returns:
            Dict suitable for agent state update: {"type:id": data, ...}

        Use this in Command(update={"ui_data": writer.get_state_update()})
        """
        return dict(self._collected_data)

    def get_all_parts(self) -> list[dict]:
        """
        Get all collected data parts as a list.

        Returns:
            List of data dicts for persisting to message additional_kwargs.
        """
        return list(self._collected_data.values())

    @property
    def has_data(self) -> bool:
        """Check if any non-transient data has been collected."""
        return len(self._collected_data) > 0
