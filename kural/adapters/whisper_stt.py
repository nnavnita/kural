"""faster-whisper STT adapter.

Selected when ``KURAL_STT_PROVIDER=whisper`` (the default). The actual
model identifier is taken from ``settings.stt_model``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from pipecat.services.ai_service import AIService

    from kural.config import Settings


class WhisperSTTAdapter:
    """STTAdapter backed by Pipecat's faster-whisper service."""

    name: ClassVar[str] = "whisper"

    @staticmethod
    def build(settings: Settings) -> AIService:
        from pipecat.services.whisper.stt import WhisperSTTService

        return WhisperSTTService(
            settings=WhisperSTTService.Settings(model=settings.stt_model),
        )
