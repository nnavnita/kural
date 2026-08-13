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
    from fastapi import Request, Response
    from pipecat.serializers.base_serializer import FrameSerializer
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


@runtime_checkable
class TelephonyAdapter(Protocol):
    """Bridges a telephony provider's call-media protocol to a Pipecat pipeline.

    Unlike the LLM/STT/TTS adapters (one ``build`` call each), a telephony
    provider needs to participate in the inbound webhook, the outbound
    dial, and the per-call media serializer — so the protocol has three
    methods instead of one.
    """

    name: ClassVar[str]

    @staticmethod
    def verify_webhook(request: Request, body: bytes, settings: Settings) -> bool:
        """Verify an inbound webhook request was sent by the provider."""
        ...

    @staticmethod
    def handle_inbound_webhook(request: Request, media_stream_url: str) -> Response:
        """Build the provider-specific response that accepts the call.

        ``media_stream_url`` is the ``wss://`` URL the provider should
        open a media-stream WebSocket connection to.
        """
        ...

    @staticmethod
    def build_serializer(call_sid: str, stream_sid: str, settings: Settings) -> FrameSerializer:
        """Build the Pipecat :class:`FrameSerializer` for one call's media stream."""
        ...

    @staticmethod
    def place_outbound_call(to: str, settings: Settings, webhook_url: str) -> str:
        """Dial ``to`` via the provider's REST API. Returns the provider call ID."""
        ...
