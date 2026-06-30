"""Tests for the LLM/STT/TTS adapters and the provider registries.

The adapters import heavyweight Pipecat services lazily inside their
``build`` methods so each test can stub the relevant submodule via
``sys.modules`` without pulling model weights into memory.
"""

from __future__ import annotations

import sys
import types
from unittest.mock import MagicMock

import pytest

from kural.adapters import (
    LLM_PROVIDERS,
    STT_PROVIDERS,
    TTS_PROVIDERS,
    LLMAdapter,
    STTAdapter,
    TTSAdapter,
)
from kural.adapters.openai_llm import OpenAILLMAdapter
from kural.adapters.piper_tts import PiperTTSAdapter
from kural.adapters.whisper_stt import WhisperSTTAdapter
from tests.conftest import make_settings


def _install_fake_module(monkeypatch: pytest.MonkeyPatch, dotted: str) -> types.ModuleType:
    module = types.ModuleType(dotted)
    monkeypatch.setitem(sys.modules, dotted, module)
    parts = dotted.split(".")
    for i in range(1, len(parts)):
        parent = ".".join(parts[:i])
        if parent not in sys.modules:
            monkeypatch.setitem(sys.modules, parent, types.ModuleType(parent))
    return module


# --- Protocol conformance -------------------------------------------------


def test_openai_llm_adapter_satisfies_llm_protocol() -> None:
    assert isinstance(OpenAILLMAdapter, LLMAdapter)


def test_whisper_stt_adapter_satisfies_stt_protocol() -> None:
    assert isinstance(WhisperSTTAdapter, STTAdapter)


def test_piper_tts_adapter_satisfies_tts_protocol() -> None:
    assert isinstance(PiperTTSAdapter, TTSAdapter)


# --- Registry wiring ------------------------------------------------------


def test_default_llm_provider_is_registered() -> None:
    assert LLM_PROVIDERS["openai"] is OpenAILLMAdapter


def test_default_stt_provider_is_registered() -> None:
    assert STT_PROVIDERS["whisper"] is WhisperSTTAdapter


def test_default_tts_provider_is_registered() -> None:
    assert TTS_PROVIDERS["piper"] is PiperTTSAdapter


# --- Concrete adapter build behaviour ------------------------------------


def test_openai_llm_adapter_constructs_pipecat_service(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_module = _install_fake_module(monkeypatch, "pipecat.services.openai.llm")
    service_cls = MagicMock(name="OpenAILLMService")
    fake_module.OpenAILLMService = service_cls  # type: ignore[attr-defined]

    settings = make_settings(
        llm_model="llama3.1",
        llm_api_key="sk-test",
        llm_base_url="http://localhost:11434/v1",
    )
    result = OpenAILLMAdapter.build(settings)

    service_cls.assert_called_once_with(
        model="llama3.1",
        api_key="sk-test",
        base_url="http://localhost:11434/v1",
    )
    assert result is service_cls.return_value


def test_whisper_stt_adapter_constructs_pipecat_service(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_module = _install_fake_module(monkeypatch, "pipecat.services.whisper.stt")
    settings_cls = MagicMock(name="WhisperSTTSettings")
    service_cls = MagicMock(name="WhisperSTTService")
    service_cls.Settings = settings_cls
    fake_module.WhisperSTTService = service_cls  # type: ignore[attr-defined]

    result = WhisperSTTAdapter.build(make_settings(stt_model="tiny.en"))

    settings_cls.assert_called_once_with(model="tiny.en")
    service_cls.assert_called_once_with(settings=settings_cls.return_value)
    assert result is service_cls.return_value


def test_piper_tts_adapter_constructs_pipecat_service(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_module = _install_fake_module(monkeypatch, "pipecat.services.piper.tts")
    settings_cls = MagicMock(name="PiperTTSSettings")
    service_cls = MagicMock(name="PiperTTSService")
    service_cls.Settings = settings_cls
    fake_module.PiperTTSService = service_cls  # type: ignore[attr-defined]

    result = PiperTTSAdapter.build(make_settings(tts_voice="en_US-ryan-high"))

    settings_cls.assert_called_once_with(voice="en_US-ryan-high")
    service_cls.assert_called_once_with(settings=settings_cls.return_value)
    assert result is service_cls.return_value
