"""AgentRunner - Manages chat agent lifecycle with caching based on AI Settings.

This module provides the AgentRunner class which handles:
- AI Settings loading and caching
- Knowledge base initialization
- Agent creation with proper middleware
- Thread permission management
- Running agent in UI mode with SSE streaming
"""

from __future__ import annotations

from typing import Any, ClassVar, Generator

import frappe
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig

from gms.ai.agents_v2.agents.chat_agent import create_chat_agent
from gms.ai.agents_v2.checkpointer.frappe_in import FrappeBufferedCheckpointer
from gms.ai.agents_v2.vercel_ui.converter import convert_messages_to_ui_messages
from gms.ai.agents_v2.vercel_ui.stream_handler import VercelUIStreamHandler
from gms.ai.kb.kb import Knowledge


class AgentRunner:
    """Manages chat agent lifecycle with caching based on AI Settings.

    The agent and Knowledge instance are cached at the class level based on
    the AI Settings `modified` timestamp. When settings change, the cache
    is invalidated and new instances are created.

    Usage:
        # Run a query
        runner = AgentRunner(thread_id="existing-thread-id")
        for chunk in runner.run_ui_mode("What is ChákṣuAI?"):
            yield chunk

        # Get history
        runner = AgentRunner(thread_id="existing-thread-id")
        messages = runner.get_history()
    """

    # Class-level cache: {settings_modified: Knowledge}
    _cache: ClassVar[dict[str, Knowledge]] = {}
    _cache_key: ClassVar[str | None] = None

    def __init__(self, thread_id: str | None = None):
        """Initialize AgentRunner with optional thread ID.

        Args:
            thread_id: Optional existing thread ID. If None, a new thread
                      will be created on first run.

        Raises:
            frappe.PermissionError: If user doesn't have access to the thread
        """
        self.thread_id = thread_id
        self.thread = None
        self._is_new_thread = False

        # Load and check thread permissions if thread_id provided
        if thread_id:
            self.thread = frappe.get_doc("AI Thread", thread_id)
            self.thread.check_permission()

        # Get cached knowledge (or create new if settings changed)
        self.knowledge = self._get_cached_knowledge()

    @classmethod
    def _get_cached_knowledge(cls) -> Knowledge:
        """Get cached Knowledge instance, or create new if settings changed.

        Returns:
            Knowledge instance configured from AI Settings
        """
        settings = frappe.get_single("AI Settings")
        cache_key = str(settings.modified)

        # Check if cache is valid
        if cls._cache_key != cache_key:
            # Invalidate old cache
            cls._cache.clear()
            cls._cache_key = cache_key

            # Create new Knowledge instance
            knowledge = Knowledge(
                uri=settings.milvus_db_url,
                token=settings.milvus_db_token,
            )
            cls._cache[cache_key] = knowledge
            print(
                f"AgentRunner: Created new Knowledge instance (settings modified: {cache_key})"
            )

        return cls._cache[cache_key]

    @classmethod
    def invalidate_cache(cls) -> None:
        """Force invalidation of the cached Knowledge instance."""
        cls._cache.clear()
        cls._cache_key = None

    def _ensure_thread(self) -> None:
        """Ensure thread exists, creating one if necessary."""
        if self.thread is None:
            self.thread = frappe.new_doc("AI Thread")
            self.thread.title = "New Chat"
            self.thread.save()
            self.thread_id = self.thread.name
            self._is_new_thread = True
            frappe.db.commit()

    def _save_thread(self) -> None:
        """Save thread if it exists."""
        if self.thread:
            self.thread.save()
            frappe.db.commit()

    def run_ui_mode(self, query: str) -> Generator[str, None, None]:
        """Run agent in UI mode, returning SSE stream.

        Args:
            query: User query to process

        Yields:
            SSE formatted chunks for streaming response
        """
        if not query:
            raise ValueError("Query is required")

        # Ensure we have a thread
        self._ensure_thread()

        config: RunnableConfig = {"configurable": {"thread_id": self.thread_id}}
        checkpointer = FrappeBufferedCheckpointer()
        checkpointer.load_from_frappe(config)

        agent = create_chat_agent(self.knowledge, checkpointer=checkpointer)
        state = {"messages": [HumanMessage(content=query)]}

        handler = VercelUIStreamHandler()

        # Start stream
        yield from handler.start()

        # Process agent stream
        # Filter by namespace: () = main agent, ('subagent-name',) = subagent
        for namespace, stream_mode, data in agent.stream(
            state,
            config,
            stream_mode=["messages", "custom"],
            subgraphs=True,
        ):
            # Always process custom events (from middleware write_data calls)
            # Only filter message events to main agent namespace
            if stream_mode == "custom" or namespace == ():
                yield from handler.process_event(stream_mode, data)

        # Get final state for thread title update
        # Note: Steps persistence is handled by StepsMiddleware.after_agent
        final_state = agent.get_state(config)

        # Update thread title if generated and thread has default title
        thread_title = final_state.values.get("thread_title")
        if thread_title and self.thread and self.thread.has_default_title():
            self.thread.title = thread_title
            print(f"Updated thread title: {thread_title}")

        # Save thread after stream completes
        self._save_thread()

        # Flush checkpointer data at the very end
        checkpointer.flush_to_frappe()

        # Finish stream
        yield from handler.finish()

    def get_history(self) -> list[dict[str, Any]]:
        """Get chat history for the thread.

        Returns:
            List of UI messages in Vercel AI format

        Raises:
            ValueError: If no thread_id was provided
        """
        if not self.thread_id:
            raise ValueError("Thread ID is required to get history")

        config: RunnableConfig = {"configurable": {"thread_id": self.thread_id}}
        checkpointer = FrappeBufferedCheckpointer()
        checkpointer.load_from_frappe(config)

        agent = create_chat_agent(self.knowledge, checkpointer=checkpointer)
        state = agent.get_state(config)
        messages = state.values.get("messages", [])

        return convert_messages_to_ui_messages(messages)
