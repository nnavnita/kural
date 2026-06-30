"""Factory functions for the STT/LLM/TTS services used by the voice pipeline.

These wrappers exist so :mod:`kural.pipeline` does not need to import
heavyweight model libraries at module-import time, and so tests can
``monkeypatch`` each factory without standing up a real model.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pipecat.services.ai_service import AIService

from kural.config import Settings


def build_stt(settings: Settings) -> AIService:
    """Build the speech-to-text service (faster-whisper)."""
    from pipecat.services.whisper.stt import WhisperSTTService

    return WhisperSTTService(
        settings=WhisperSTTService.Settings(model=settings.stt_model),
    )


def build_llm(settings: Settings) -> AIService:
    """Build the LLM service (OpenAI-compatible)."""
    from pipecat.services.openai.llm import OpenAILLMService

    return OpenAILLMService(
        model=settings.llm_model,
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
    )


def build_tts(settings: Settings) -> AIService:
    """Build the text-to-speech service (Piper).

    Piper is used as the default local TTS because it ships pure-ABI3
    wheels that cover Python 3.14; Kokoro (``kokoro-onnx``) currently
    pins ``<3.14`` and so cannot be installed on this project's target
    interpreter. Swapping providers is a one-line change here.
    """
    from pipecat.services.piper.tts import PiperTTSService

    return PiperTTSService(
        settings=PiperTTSService.Settings(voice=settings.tts_voice),
    )
