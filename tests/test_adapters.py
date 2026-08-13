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
from kural.adapters.deepgram_stt import DeepgramSTTAdapter
from kural.adapters.elevenlabs_tts import ElevenLabsTTSAdapter
from kural.adapters.kokoro_tts import KokoroTTSAdapter
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


def test_deepgram_stt_adapter_satisfies_stt_protocol() -> None:
    assert isinstance(DeepgramSTTAdapter, STTAdapter)


def test_piper_tts_adapter_satisfies_tts_protocol() -> None:
    assert isinstance(PiperTTSAdapter, TTSAdapter)


def test_elevenlabs_tts_adapter_satisfies_tts_protocol() -> None:
    assert isinstance(ElevenLabsTTSAdapter, TTSAdapter)


def test_kokoro_tts_adapter_satisfies_tts_protocol() -> None:
    assert isinstance(KokoroTTSAdapter, TTSAdapter)


# --- Registry wiring ------------------------------------------------------


def test_default_llm_provider_is_registered() -> None:
    assert LLM_PROVIDERS["openai"] is OpenAILLMAdapter


def test_default_stt_provider_is_registered() -> None:
    assert STT_PROVIDERS["whisper"] is WhisperSTTAdapter


def test_deepgram_stt_provider_is_registered() -> None:
    assert STT_PROVIDERS["deepgram"] is DeepgramSTTAdapter


def test_default_tts_provider_is_registered() -> None:
    assert TTS_PROVIDERS["piper"] is PiperTTSAdapter


def test_elevenlabs_tts_provider_is_registered() -> None:
    assert TTS_PROVIDERS["elevenlabs"] is ElevenLabsTTSAdapter


def test_kokoro_tts_provider_is_registered() -> None:
    assert TTS_PROVIDERS["kokoro"] is KokoroTTSAdapter


# --- STT contract: every STT adapter must satisfy this identically -------


@pytest.mark.parametrize(
    ("adapter_cls", "module_path", "service_name"),
    [
        (WhisperSTTAdapter, "pipecat.services.whisper.stt", "WhisperSTTService"),
        (DeepgramSTTAdapter, "pipecat.services.deepgram.stt", "DeepgramSTTService"),
    ],
)
def test_stt_adapter_contract(
    adapter_cls: type[STTAdapter],
    module_path: str,
    service_name: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Every STT adapter: satisfies the Protocol, is registered under its own
    ``name``, and ``build`` returns the Pipecat service it constructs — without
    ever touching a live API.
    """
    assert isinstance(adapter_cls, STTAdapter)
    assert STT_PROVIDERS[adapter_cls.name] is adapter_cls

    fake_module = _install_fake_module(monkeypatch, module_path)
    service_cls = MagicMock(name=service_name)
    service_cls.Settings = MagicMock(name=f"{service_name}.Settings")
    setattr(fake_module, service_name, service_cls)

    result = adapter_cls.build(make_settings(stt_provider=adapter_cls.name, stt_model="test-model"))

    service_cls.Settings.assert_called_once_with(model="test-model")
    assert result is service_cls.return_value


# --- TTS contract: every TTS adapter must satisfy this identically -------


@pytest.mark.parametrize(
    ("adapter_cls", "module_path", "service_name"),
    [
        (PiperTTSAdapter, "pipecat.services.piper.tts", "PiperTTSService"),
        (ElevenLabsTTSAdapter, "pipecat.services.elevenlabs.tts", "ElevenLabsTTSService"),
        (KokoroTTSAdapter, "pipecat.services.kokoro.tts", "KokoroTTSService"),
    ],
)
def test_tts_adapter_contract(
    adapter_cls: type[TTSAdapter],
    module_path: str,
    service_name: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Every TTS adapter: satisfies the Protocol, is registered under its own
    ``name``, and ``build`` returns the Pipecat service it constructs from
    ``settings.tts_voice`` — without ever touching a live API.
    """
    assert isinstance(adapter_cls, TTSAdapter)
    assert TTS_PROVIDERS[adapter_cls.name] is adapter_cls

    fake_module = _install_fake_module(monkeypatch, module_path)
    service_cls = MagicMock(name=service_name)
    service_cls.Settings = MagicMock(name=f"{service_name}.Settings")
    setattr(fake_module, service_name, service_cls)

    result = adapter_cls.build(make_settings(tts_provider=adapter_cls.name, tts_voice="test-voice"))

    service_cls.Settings.assert_called_once_with(voice="test-voice")
    assert result is service_cls.return_value


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


def test_deepgram_stt_adapter_constructs_pipecat_service(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_module = _install_fake_module(monkeypatch, "pipecat.services.deepgram.stt")
    settings_cls = MagicMock(name="DeepgramSTTSettings")
    service_cls = MagicMock(name="DeepgramSTTService")
    service_cls.Settings = settings_cls
    fake_module.DeepgramSTTService = service_cls  # type: ignore[attr-defined]

    result = DeepgramSTTAdapter.build(
        make_settings(stt_model="nova-3-general", deepgram_api_key="dg-test-key"),
    )

    settings_cls.assert_called_once_with(model="nova-3-general")
    service_cls.assert_called_once_with(
        api_key="dg-test-key",
        settings=settings_cls.return_value,
    )
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


def test_elevenlabs_tts_adapter_constructs_pipecat_service(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_module = _install_fake_module(monkeypatch, "pipecat.services.elevenlabs.tts")
    settings_cls = MagicMock(name="ElevenLabsTTSSettings")
    service_cls = MagicMock(name="ElevenLabsTTSService")
    service_cls.Settings = settings_cls
    fake_module.ElevenLabsTTSService = service_cls  # type: ignore[attr-defined]

    result = ElevenLabsTTSAdapter.build(
        make_settings(tts_voice="Rachel", elevenlabs_api_key="el-test-key"),
    )

    settings_cls.assert_called_once_with(voice="Rachel")
    service_cls.assert_called_once_with(
        api_key="el-test-key",
        settings=settings_cls.return_value,
    )
    assert result is service_cls.return_value


def test_kokoro_tts_adapter_constructs_pipecat_service(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_module = _install_fake_module(monkeypatch, "pipecat.services.kokoro.tts")
    settings_cls = MagicMock(name="KokoroTTSSettings")
    service_cls = MagicMock(name="KokoroTTSService")
    service_cls.Settings = settings_cls
    fake_module.KokoroTTSService = service_cls  # type: ignore[attr-defined]

    result = KokoroTTSAdapter.build(make_settings(tts_voice="af_heart"))

    settings_cls.assert_called_once_with(voice="af_heart")
    service_cls.assert_called_once_with(settings=settings_cls.return_value)
    assert result is service_cls.return_value
