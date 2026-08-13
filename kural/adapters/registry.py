"""Provider registries for the LLM, STT, and TTS layers.

Each registry maps the env-facing provider name (e.g. ``"openai"``,
``"whisper"``, ``"piper"``) to the adapter class that implements the
corresponding Protocol from :mod:`kural.adapters.base`.

To add a new provider, write an adapter class in this package and
append it here. No edits to :mod:`kural.services` or
:mod:`kural.pipeline` are required.
"""

from __future__ import annotations

from kural.adapters.base import LLMAdapter, STTAdapter, TelephonyAdapter, TTSAdapter
from kural.adapters.openai_llm import OpenAILLMAdapter
from kural.adapters.piper_tts import PiperTTSAdapter
from kural.adapters.twilio_tel import TwilioTelephonyAdapter
from kural.adapters.whisper_stt import WhisperSTTAdapter

LLM_PROVIDERS: dict[str, type[LLMAdapter]] = {
    OpenAILLMAdapter.name: OpenAILLMAdapter,
}

STT_PROVIDERS: dict[str, type[STTAdapter]] = {
    WhisperSTTAdapter.name: WhisperSTTAdapter,
}

TTS_PROVIDERS: dict[str, type[TTSAdapter]] = {
    PiperTTSAdapter.name: PiperTTSAdapter,
}

TELEPHONY_PROVIDERS: dict[str, type[TelephonyAdapter]] = {
    TwilioTelephonyAdapter.name: TwilioTelephonyAdapter,
}
