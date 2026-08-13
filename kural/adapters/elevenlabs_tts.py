"""ElevenLabs TTS adapter.

Selected via ``KURAL_TTS_PROVIDER=elevenlabs``. Requires
``ELEVENLABS_API_KEY``. Voice id comes from ``settings.tts_voice`` — same
knob ``PiperTTSAdapter`` uses, so switching providers is one env var.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from pipecat.services.ai_service import AIService

    from kural.config import Settings


class ElevenLabsTTSAdapter:
    """TTSAdapter backed by Pipecat's ElevenLabs service."""

    name: ClassVar[str] = "elevenlabs"

    @staticmethod
    def build(settings: Settings) -> AIService:
        from pipecat.services.elevenlabs.tts import ElevenLabsTTSService

        return ElevenLabsTTSService(
            api_key=settings.elevenlabs_api_key,
            settings=ElevenLabsTTSService.Settings(voice=settings.tts_voice),
        )
