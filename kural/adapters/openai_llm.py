"""OpenAI-compatible LLM adapter.

Works against any provider that speaks the OpenAI Chat Completions wire
format — OpenAI, OpenRouter, Groq, Together, Ollama, vLLM, llama.cpp's
OpenAI server, etc. The provider is chosen by pointing
``KURAL_LLM_BASE_URL`` at the right endpoint.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from pipecat.services.ai_service import AIService

    from kural.config import Settings


class OpenAILLMAdapter:
    """LLMAdapter for any OpenAI-compatible HTTP endpoint."""

    name: ClassVar[str] = "openai"

    @staticmethod
    def build(settings: Settings) -> AIService:
        from pipecat.services.openai.llm import OpenAILLMService

        return OpenAILLMService(
            model=settings.llm_model,
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
        )
