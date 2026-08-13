"""Deepgram STT adapter.

Selected via ``KURAL_STT_PROVIDER=deepgram``. Requires ``DEEPGRAM_API_KEY``.
The model identifier is taken from ``settings.stt_model`` — same knob
``WhisperSTTAdapter`` uses, so switching providers is one env var.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from pipecat.services.ai_service import AIService

    from kural.config import Settings


class DeepgramSTTAdapter:
    """STTAdapter backed by Pipecat's Deepgram service."""

    name: ClassVar[str] = "deepgram"

    @staticmethod
    def build(settings: Settings) -> AIService:
        from pipecat.services.deepgram.stt import DeepgramSTTService

        return DeepgramSTTService(
            api_key=settings.deepgram_api_key,
            settings=DeepgramSTTService.Settings(model=settings.stt_model),
        )
