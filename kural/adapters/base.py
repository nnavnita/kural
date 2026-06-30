"""Adapter Protocols for the LLM, STT, and TTS layers.

Each Protocol describes the single contract every concrete adapter must
satisfy: a ``build`` staticmethod that returns a Pipecat
:class:`~pipecat.services.ai_service.AIService` constructed from the
runtime :class:`~kural.config.Settings`.

The Protocols are intentionally tiny so that adding a new provider is
just "write a class with one ``build`` method, register it" — no base
class to subclass, no lifecycle hooks to remember.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Protocol, runtime_checkable

if TYPE_CHECKING:
    from pipecat.services.ai_service import AIService

    from kural.config import Settings


@runtime_checkable
class LLMAdapter(Protocol):
    """Builds the LLM service for the voice pipeline."""

    name: ClassVar[str]

    @staticmethod
    def build(settings: Settings) -> AIService: ...


@runtime_checkable
class STTAdapter(Protocol):
    """Builds the speech-to-text service for the voice pipeline."""

    name: ClassVar[str]

    @staticmethod
    def build(settings: Settings) -> AIService: ...


@runtime_checkable
class TTSAdapter(Protocol):
    """Builds the text-to-speech service for the voice pipeline."""

    name: ClassVar[str]

    @staticmethod
    def build(settings: Settings) -> AIService: ...
