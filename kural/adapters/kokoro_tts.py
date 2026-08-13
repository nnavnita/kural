"""Kokoro TTS adapter.

Selected via ``KURAL_TTS_PROVIDER=kokoro``. Fully local (kokoro-onnx),
no API key — model/voices files auto-download on first use, same as
Whisper and Piper. Voice id comes from ``settings.tts_voice``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from pipecat.services.ai_service import AIService

    from kural.config import Settings


class KokoroTTSAdapter:
    """TTSAdapter backed by Pipecat's Kokoro service."""

    name: ClassVar[str] = "kokoro"

    @staticmethod
    def build(settings: Settings) -> AIService:
        from pipecat.services.kokoro.tts import KokoroTTSService

        return KokoroTTSService(
            settings=KokoroTTSService.Settings(voice=settings.tts_voice),
        )
