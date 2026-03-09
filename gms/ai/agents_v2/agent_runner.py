"""AgentRunner - Manages chat agent lifecycle with caching based on AI Settings.

This module provides the AgentRunner class which handles:
- AI Agent document loading and caching
- AI Settings loading and caching
- Knowledge base initialization
- Agent creation with proper middleware
- Thread permission management
- Running agent in UI mode with SSE streaming
"""

from __future__ import annotations

import traceback
from typing import Any, ClassVar, Generator

import frappe
from langchain_core.messages import AIMessageChunk, HumanMessage
from langchain_core.runnables import RunnableConfig

from gms.ai.agents_v2.agents.chat_agent import create_chat_agent
from gms.ai.agents_v2.checkpointer.frappe_in import FrappeBufferedCheckpointer
from gms.ai.agents_v2.vercel_ui.converter import convert_messages_to_ui_messages
from gms.ai.agents_v2.vercel_ui.stream_handler import VercelUIStreamHandler
from gms.ai.kb.kb import Knowledge


class AgentRunner:
    """Manages chat agent lifecycle with caching based on AI Settings.

    The Knowledge instance is cached at the class level based on
    the AI Settings `modified` timestamp. When settings change, the cache
    is invalidated and new instances are created.

    Usage:
        runner = AgentRunner()

        # Run a query
        for chunk in runner.run_ui_mode("agent-123", "thread-456", "What is ChákṣuAI?"):
            yield chunk

        # Get history (no agent_id needed)
        messages = runner.get_history("thread-456")
    """

    # Class-level cache: {cache_key: Knowledge}
    _knowledge_cache: ClassVar[dict[str, Knowledge]] = {}
    _knowledge_cache_key: ClassVar[str | None] = None

    def __init__(self):
        """Initialize AgentRunner."""
        # Get cached knowledge (or create new if settings changed)
        self.knowledge = self._get_cached_knowledge()

    @classmethod
    def _get_cached_knowledge(cls) -> Knowledge:
        """Get cached Knowledge instance, or create new if settings changed.

        Returns:
            Knowledge instance configured from AI Settings
        """
        # Use get_cached_value for AI Settings fields (SingleDocType)
        modified = frappe.get_cached_value("AI Settings", "AI Settings", "modified")
        cache_key = str(modified)

        # Check if cache is valid
        if cls._knowledge_cache_key != cache_key:
            # Invalidate old cache
            cls._knowledge_cache.clear()
            cls._knowledge_cache_key = cache_key

            # Get cached values for settings
            milvus_db_url = frappe.get_cached_value(
                "AI Settings", "AI Settings", "milvus_db_url"
            )
            milvus_db_token = frappe.get_cached_value(
                "AI Settings", "AI Settings", "milvus_db_token"
            )

            collection_name = frappe.get_cached_value(
                "AI Settings", "AI Settings", "milvus_kb_collection"
            )

            # Create new Knowledge instance
            knowledge = Knowledge(
                uri=milvus_db_url,
                token=milvus_db_token,
                collection_name=collection_name
            )
            cls._knowledge_cache[cache_key] = knowledge
            print(
                f"AgentRunner: Created new Knowledge instance (settings modified: {cache_key})"
            )

        return cls._knowledge_cache[cache_key]

    @classmethod
    def invalidate_cache(cls) -> None:
        """Force invalidation of the cached Knowledge instance."""
        cls._knowledge_cache.clear()
        cls._knowledge_cache_key = None

    def run_ui_mode(
        self, ai_agent_id: str, thread_id: str | None, query: str, context: str
    ) -> Generator[str, None, None]:
        """Run agent in UI mode, returning SSE stream.

        Args:
            ai_agent_id: The ID of the AI Agent document to use
            thread_id: Optional existing thread ID. If None, a new thread will be created.
            query: User query to process

        Yields:
            SSE formatted chunks for streaming response
        """
        if not query:
            raise ValueError("Query is required")

        # Load or create thread
        thread = None
        if thread_id:
            thread = frappe.get_doc("AI Thread", thread_id)
            thread.check_permission()
        else:
            thread = frappe.new_doc("AI Thread")
            thread.title = "New Chat"
            thread.save()
            thread_id = thread.name
            frappe.db.commit()

        config: RunnableConfig = {"configurable": {"thread_id": thread_id}}
        checkpointer = FrappeBufferedCheckpointer()
        checkpointer.load_from_frappe(config)

        handler = VercelUIStreamHandler(include_types=["text", "data", "tool"])



        agent = create_chat_agent(
            ai_agent_id=ai_agent_id,
            knowledge=self.knowledge,
            checkpointer=checkpointer,
            context=context
        )
        state = {"messages": [HumanMessage(content=query)]}

        # Start stream
        yield from handler.start()

        try:
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
            if thread_title and thread and thread.has_default_title():
                thread.title = thread_title
                print(f"Updated thread title: {thread_title}")

            # Save thread after stream completes
            if thread:
                thread.save()
                frappe.db.commit()

            # Flush checkpointer data at the very end
            checkpointer.flush_to_frappe()

        except Exception as e:
            traceback.print_exception(e)
            # Log error
            print(f"Agent execution error: {e}")

            # Yield error event as per Vercel AI SDK protocol
            yield handler.encode_error(str(e))

        # Always finish stream (even on error)
        yield from handler.finish()

    def get_history(self, thread_id: str) -> list[dict[str, Any]]:
        """Get chat history for the thread.

        Args:
            thread_id: The thread ID to get history for

        Returns:
            List of UI messages in Vercel AI format
        """
        if not thread_id:
            raise ValueError("Thread ID is required to get history")

        # Check thread permissions
        thread = frappe.get_doc("AI Thread", thread_id)
        thread.check_permission()

        config: RunnableConfig = {"configurable": {"thread_id": thread_id}}
        checkpointer = FrappeBufferedCheckpointer()
        checkpointer.load_from_frappe(config)

        # For history, we just need the checkpointer state, no agent needed
        state = checkpointer.get(config)
        messages = state.get("channel_values", {}).get("messages", []) if state else []

        # Match the filtering used in run_ui_mode (text and data only)
        return convert_messages_to_ui_messages(messages, include_types=["text", "data"])
