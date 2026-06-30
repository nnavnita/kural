"""Service factories for the voice pipeline.

Each ``build_*`` function resolves the provider name in
:class:`~kural.config.Settings` against the matching registry in
:mod:`kural.adapters.registry` and delegates construction to that
adapter. The pipeline never sees the underlying Pipecat class, so
swapping providers is a one-env-var change.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from kural.adapters.registry import LLM_PROVIDERS, STT_PROVIDERS, TTS_PROVIDERS
from kural.config import Settings

if TYPE_CHECKING:
    from pipecat.services.ai_service import AIService


def _resolve(registry: dict[str, type], name: str, layer: str) -> type:
    try:
        return registry[name]
    except KeyError as err:
        available = ", ".join(sorted(registry)) or "(none registered)"
        raise ValueError(
            f"unknown {layer} provider {name!r}; registered: {available}",
        ) from err


def build_stt(settings: Settings) -> AIService:
    """Build the STT service for ``settings.stt_provider``."""
    adapter = _resolve(STT_PROVIDERS, settings.stt_provider, "STT")
    return adapter.build(settings)


def build_llm(settings: Settings) -> AIService:
    """Build the LLM service for ``settings.llm_provider``."""
    adapter = _resolve(LLM_PROVIDERS, settings.llm_provider, "LLM")
    return adapter.build(settings)


def build_tts(settings: Settings) -> AIService:
    """Build the TTS service for ``settings.tts_provider``."""
    adapter = _resolve(TTS_PROVIDERS, settings.tts_provider, "TTS")
    return adapter.build(settings)
