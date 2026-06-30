"""Runtime configuration loaded from environment variables.

All settings are read once at startup via :meth:`Settings.from_env`, which
also loads a ``.env`` file (if present) using :mod:`python-dotenv`.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal

from dotenv import load_dotenv

AgentMode = Literal["echo", "voice"]

_DEFAULT_AGENT_PROMPT = (
    "You are kural, a concise and friendly voice assistant. "
    "Keep replies under two short sentences so they can be spoken quickly."
)


@dataclass(frozen=True)
class Settings:
    """Immutable container for the values the runtime needs.

    Attributes:
        mode: Which pipeline to run — ``"echo"`` (v0 passthrough) or
            ``"voice"`` (v0.1 STT → LLM → TTS loop).
        sample_rate: Sample rate (Hz) used by the audio input side of the
            local transport. 16 kHz is the Pipecat default and matches
            Whisper/Silero.
        output_sample_rate: Sample rate (Hz) used by the audio output side
            of the local transport. Kept separate from the input rate so
            TTS playback can run at 24 kHz (less choppy than resampling
            down to 16 kHz) while STT still consumes 16 kHz audio.
        log_level: loguru log level (``DEBUG``, ``INFO``, ``WARNING``, ...).
        llm_base_url: OpenAI-compatible LLM endpoint. ``None`` selects
            the OpenAI default. Point at OpenRouter, Ollama, vLLM, etc.
            for self-hosted or alternate providers.
        llm_api_key: API key for the LLM endpoint. May be ``None`` for
            local providers (Ollama, vLLM) that ignore auth.
        llm_provider: Registry key selecting the LLM adapter to build
            (see :data:`kural.adapters.registry.LLM_PROVIDERS`). Defaults
            to ``"openai"`` — any OpenAI-compatible HTTP endpoint.
        llm_model: Model identifier passed to the LLM provider.
        stt_provider: Registry key selecting the STT adapter to build
            (see :data:`kural.adapters.registry.STT_PROVIDERS`). Defaults
            to ``"whisper"`` (faster-whisper).
        stt_model: faster-whisper model identifier.
        tts_provider: Registry key selecting the TTS adapter to build
            (see :data:`kural.adapters.registry.TTS_PROVIDERS`). Defaults
            to ``"piper"``.
        tts_voice: Piper voice identifier (e.g. ``en_US-amy-medium``).
        agent_prompt: System prompt seeded into the LLM context.
    """

    mode: AgentMode
    sample_rate: int
    output_sample_rate: int
    log_level: str
    llm_provider: str
    llm_base_url: str | None
    llm_api_key: str | None
    llm_model: str
    stt_provider: str
    stt_model: str
    tts_provider: str
    tts_voice: str
    agent_prompt: str

    @classmethod
    def from_env(cls) -> Settings:
        """Construct a :class:`Settings` from environment variables.

        Loads ``.env`` if present. Recognised variables:

        - ``KURAL_MODE`` (``echo``|``voice``, default ``voice``)
        - ``KURAL_SAMPLE_RATE`` (int, default ``16000``) — audio input rate.
        - ``KURAL_OUTPUT_SAMPLE_RATE`` (int, default ``24000``) — audio
          output rate; matches TTS native rate more closely than 16 kHz.
        - ``KURAL_LOG_LEVEL`` (str, default ``INFO``; upper-cased)
        - ``KURAL_LLM_PROVIDER`` (str, default ``openai``) — registry key.
        - ``KURAL_LLM_BASE_URL`` (str, optional)
        - ``KURAL_LLM_API_KEY`` (str, optional)
        - ``KURAL_LLM_MODEL`` (str, default ``gpt-4o-mini``)
        - ``KURAL_STT_PROVIDER`` (str, default ``whisper``) — registry key.
        - ``KURAL_STT_MODEL`` (str, default ``distil-medium.en``)
        - ``KURAL_TTS_PROVIDER`` (str, default ``piper``) — registry key.
        - ``KURAL_TTS_VOICE`` (str, default ``en_US-amy-medium``)
        - ``KURAL_AGENT_PROMPT`` (str, default friendly assistant prompt)
        """
        load_dotenv()
        return cls(
            mode=_parse_mode(os.getenv("KURAL_MODE", "voice")),
            sample_rate=int(os.getenv("KURAL_SAMPLE_RATE", "16000")),
            output_sample_rate=int(os.getenv("KURAL_OUTPUT_SAMPLE_RATE", "24000")),
            log_level=os.getenv("KURAL_LOG_LEVEL", "INFO").upper(),
            llm_provider=os.getenv("KURAL_LLM_PROVIDER", "openai"),
            llm_base_url=os.getenv("KURAL_LLM_BASE_URL") or None,
            llm_api_key=os.getenv("KURAL_LLM_API_KEY") or None,
            llm_model=os.getenv("KURAL_LLM_MODEL", "gpt-4o-mini"),
            stt_provider=os.getenv("KURAL_STT_PROVIDER", "whisper"),
            stt_model=os.getenv("KURAL_STT_MODEL", "distil-medium.en"),
            tts_provider=os.getenv("KURAL_TTS_PROVIDER", "piper"),
            tts_voice=os.getenv("KURAL_TTS_VOICE", "en_US-amy-medium"),
            agent_prompt=os.getenv("KURAL_AGENT_PROMPT", _DEFAULT_AGENT_PROMPT),
        )


def _parse_mode(raw: str) -> AgentMode:
    value = raw.strip().lower()
    if value not in {"echo", "voice"}:
        raise ValueError(
            f"KURAL_MODE must be 'echo' or 'voice', got {raw!r}",
        )
    return value  # type: ignore[return-value]
