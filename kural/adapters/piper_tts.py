"""Piper TTS adapter.

Piper is the default local TTS because it ships pure-ABI3 wheels that
cover Python 3.14. Voice id comes from ``settings.tts_voice``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from pipecat.services.ai_service import AIService

    from kural.config import Settings


class PiperTTSAdapter:
    """TTSAdapter backed by Pipecat's Piper service."""

    name: ClassVar[str] = "piper"

    @staticmethod
    def build(settings: Settings) -> AIService:
        from pipecat.services.piper.tts import PiperTTSService

        return PiperTTSService(
            settings=PiperTTSService.Settings(voice=settings.tts_voice),
        )
