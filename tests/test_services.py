"""Tests for :mod:`kural.services` factories.

The factories ``import`` the heavyweight Pipecat services lazily inside
each function so that test code can stub the relevant submodule via
``sys.modules`` without pulling model weights into memory.
"""

from __future__ import annotations

import sys
import types
from unittest.mock import MagicMock

import pytest

from kural import services
from tests.conftest import make_settings


def _install_fake_module(monkeypatch: pytest.MonkeyPatch, dotted: str) -> types.ModuleType:
    module = types.ModuleType(dotted)
    monkeypatch.setitem(sys.modules, dotted, module)
    # Ensure parents exist so ``from pkg.sub import X`` works.
    parts = dotted.split(".")
    for i in range(1, len(parts)):
        parent = ".".join(parts[:i])
        if parent not in sys.modules:
            monkeypatch.setitem(sys.modules, parent, types.ModuleType(parent))
    return module


def test_build_stt_uses_settings_model(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_module = _install_fake_module(monkeypatch, "pipecat.services.whisper.stt")
    settings_cls = MagicMock(name="WhisperSTTSettings")
    service_cls = MagicMock(name="WhisperSTTService")
    service_cls.Settings = settings_cls
    fake_module.WhisperSTTService = service_cls  # type: ignore[attr-defined]

    services.build_stt(make_settings(stt_model="tiny.en"))

    settings_cls.assert_called_once_with(model="tiny.en")
    service_cls.assert_called_once_with(settings=settings_cls.return_value)


def test_build_llm_passes_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_module = _install_fake_module(monkeypatch, "pipecat.services.openai.llm")
    service_cls = MagicMock(name="OpenAILLMService")
    fake_module.OpenAILLMService = service_cls  # type: ignore[attr-defined]

    settings = make_settings(
        llm_model="llama3.1",
        llm_api_key="sk-test",
        llm_base_url="http://localhost:11434/v1",
    )
    services.build_llm(settings)

    service_cls.assert_called_once_with(
        model="llama3.1",
        api_key="sk-test",
        base_url="http://localhost:11434/v1",
    )


def test_build_tts_uses_voice(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_module = _install_fake_module(monkeypatch, "pipecat.services.piper.tts")
    settings_cls = MagicMock(name="PiperTTSSettings")
    service_cls = MagicMock(name="PiperTTSService")
    service_cls.Settings = settings_cls
    fake_module.PiperTTSService = service_cls  # type: ignore[attr-defined]

    services.build_tts(make_settings(tts_voice="en_US-ryan-high"))

    settings_cls.assert_called_once_with(voice="en_US-ryan-high")
    service_cls.assert_called_once_with(settings=settings_cls.return_value)
