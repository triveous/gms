"""Middleware for generating conversation titles.

This middleware runs after the agent completes and generates a title
for the conversation, storing it in the agent state. The runner
is responsible for persisting the title to the database.
"""

from typing import Any

from langchain.agents.middleware import AgentMiddleware
from langchain.agents.middleware.types import AgentState
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field
from typing_extensions import NotRequired


# Default model for title generation (lightweight/fast model)
DEFAULT_TITLE_MODEL = "google_genai:gemini-2.5-flash"

# System prompt for title generation
TITLE_GENERATION_PROMPT = """Generate a concise, descriptive title for this conversation.

Rules:
- Maximum 6 words
- Be specific about the topic discussed
- Don't use quotes or punctuation at the end
- Don't start with "Title:" or similar prefixes

Respond with ONLY the title, nothing else."""


class GeneratedTitle(BaseModel):
    """Schema for structured title generation output."""

    title: str = Field(description="Short, descriptive title for the conversation")


class TitleGenerationState(AgentState):
    """Extended state with thread_title field."""

    thread_title: NotRequired[str | None]


class TitleGenerationMiddleware(AgentMiddleware[TitleGenerationState, Any]):
    """Middleware that sets and generates titles for conversations.

    This middleware has two phases:

    1. `before_agent`: Sets a default title from the first human message
       (no AI generation, just truncates the query). This ensures there's
       always a title available immediately.

    2. `after_agent`: Generates an AI-powered title from the conversation
       if no AI-generated title exists yet. This replaces the default title
       with a more descriptive one.

    The title is stored in the agent state under `thread_title`.
    StateNotifierMiddleware will automatically send the title to the frontend.

    Usage:
        agent = create_deep_agent(
            ...
            middleware=[TitleGenerationMiddleware()],
        )

    Args:
        model: Model to use for AI title generation (defaults to gemini-2.5-flash)
        prompt: Custom system prompt for title generation
        max_default_length: Max length for default title from query (default 50)
    """

    state_schema = TitleGenerationState

    def __init__(
        self,
        model: str | BaseChatModel | None = None,
        prompt: str | None = None,
        max_default_length: int = 50,
    ):
        super().__init__()
        self.model = model or DEFAULT_TITLE_MODEL
        self.prompt = prompt or TITLE_GENERATION_PROMPT
        self.max_default_length = max_default_length

    def before_agent(
        self, state: TitleGenerationState, runtime: Any
    ) -> dict[str, Any] | None:
        """Set default title from first human message before agent runs.

        This sets a quick default title without AI generation.
        StateNotifierMiddleware will send this to frontend automatically.

        Args:
            state: Current agent state with messages
            runtime: Agent runtime context

        Returns:
            State update with thread_title, or None if title already exists
        """
        # Don't override existing title
        existing_title = state.get("thread_title")
        if existing_title:
            return None

        # Get first human message as default title
        messages = state.get("messages", [])
        for msg in messages:
            if getattr(msg, "type", None) == "human":
                content = getattr(msg, "content", "")
                if content:
                    # Truncate to max length
                    if len(content) > self.max_default_length:
                        title = content[: self.max_default_length - 3].strip() + "..."
                    else:
                        title = content.strip()
                    print(f"Set default title: {title}")
                    return {"thread_title": title}
                break

        return None

    def after_agent(
        self, state: TitleGenerationState, runtime: Any
    ) -> dict[str, Any] | None:
        """Generate AI title after agent completes if no AI title exists.

        Only generates if title matches the default pattern (from query).
        Streams the new title as a custom event via UIStreamWriter.

        Args:
            state: Current agent state with messages
            runtime: Agent runtime context

        Returns:
            State update with thread_title, or None if not generated
        """
        try:
            title = self._generate_title(state)
            if title:
                # Stream title to frontend using UIStreamWriter
                from gms.ai.agents_v2.utils.ui_stream_writer import get_ui_stream_writer

                writer = get_ui_stream_writer()
                writer.write_data(
                    data_type="thread_title",
                    payload={"title": title},
                    data_id="thread_title",
                    transient=True,
                )
                print(f"Generated and streamed AI title: {title}")
                return {"thread_title": title}
        except Exception as e:
            # Don't fail the agent if title generation fails
            print(f"Title generation failed: {e}")

        return None

    def _generate_title(self, state: TitleGenerationState) -> str | None:
        """Generate a title from the conversation messages.

        Args:
            state: Agent state containing messages

        Returns:
            Generated title string or None if generation fails
        """
        messages = state.get("messages", [])
        if not messages:
            return None

        # Build conversation summary for title generation
        conversation_text = self._format_messages_for_title(messages)
        if not conversation_text:
            return None

        # Initialize model with streaming disabled
        # This prevents title generation from streaming to frontend
        from langchain.chat_models import init_chat_model

        if isinstance(self.model, str):
            model = init_chat_model(self.model, disable_streaming=True)
        else:
            model = self.model

        # Generate title using structured output
        structured_model = model.with_structured_output(GeneratedTitle)

        result = structured_model.invoke(
            [
                SystemMessage(content=self.prompt),
                HumanMessage(
                    content=f"<conversation>\n{conversation_text}\n</conversation>"
                ),
            ]
        )

        if result and result.title:
            # Clean up the title
            title = result.title.strip()
            # Limit length
            if len(title) > 100:
                title = title[:97] + "..."
            return title

        return None

    def _format_messages_for_title(self, messages: list, max_messages: int = 6) -> str:
        """Format messages for title generation prompt.

        Only includes the first few messages to keep the context small.

        Args:
            messages: List of conversation messages
            max_messages: Maximum number of messages to include

        Returns:
            Formatted conversation text
        """
        formatted_parts = []

        for msg in messages[:max_messages]:
            role = getattr(msg, "type", "unknown")
            content = getattr(msg, "content", "")

            if role == "human":
                formatted_parts.append(f"User: {content}")
            elif role == "ai":
                # Truncate long AI responses
                if len(content) > 500:
                    content = content[:500] + "..."
                formatted_parts.append(f"Assistant: {content}")

        return "\n".join(formatted_parts)
