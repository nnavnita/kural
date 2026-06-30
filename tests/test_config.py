"""Tests for :mod:`kural.config`."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from kural.config import Settings
from tests.conftest import make_settings


def test_defaults(clean_env: None) -> None:
    s = Settings.from_env()
    assert s.mode == "voice"
    assert s.sample_rate == 16000
    assert s.output_sample_rate == 24000
    assert s.log_level == "INFO"
    assert s.llm_base_url is None
    assert s.llm_api_key is None
    assert s.llm_model == "gpt-4o-mini"
    assert s.stt_model == "distil-medium.en"
    assert s.tts_voice == "en_US-amy-medium"
    assert "kural" in s.agent_prompt.lower()


def test_env_override(clean_env: None, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KURAL_MODE", "echo")
    monkeypatch.setenv("KURAL_SAMPLE_RATE", "24000")
    monkeypatch.setenv("KURAL_OUTPUT_SAMPLE_RATE", "48000")
    monkeypatch.setenv("KURAL_LOG_LEVEL", "debug")
    monkeypatch.setenv("KURAL_LLM_BASE_URL", "http://localhost:11434/v1")
    monkeypatch.setenv("KURAL_LLM_API_KEY", "sk-test")
    monkeypatch.setenv("KURAL_LLM_MODEL", "llama3.1")
    monkeypatch.setenv("KURAL_STT_MODEL", "tiny.en")
    monkeypatch.setenv("KURAL_TTS_VOICE", "en_US-ryan-high")
    monkeypatch.setenv("KURAL_AGENT_PROMPT", "Be terse.")

    s = Settings.from_env()

    assert s.mode == "echo"
    assert s.sample_rate == 24000
    assert s.output_sample_rate == 48000
    assert s.log_level == "DEBUG"
    assert s.llm_base_url == "http://localhost:11434/v1"
    assert s.llm_api_key == "sk-test"
    assert s.llm_model == "llama3.1"
    assert s.stt_model == "tiny.en"
    assert s.tts_voice == "en_US-ryan-high"
    assert s.agent_prompt == "Be terse."


def test_settings_is_frozen() -> None:
    s = make_settings()
    with pytest.raises(FrozenInstanceError):
        s.sample_rate = 48000  # type: ignore[misc]


def test_invalid_sample_rate_raises(clean_env: None, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KURAL_SAMPLE_RATE", "not-a-number")
    with pytest.raises(ValueError):
        Settings.from_env()


def test_invalid_mode_raises(clean_env: None, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KURAL_MODE", "transcribe")
    with pytest.raises(ValueError, match="KURAL_MODE"):
        Settings.from_env()


def test_empty_llm_credentials_become_none(
    clean_env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("KURAL_LLM_BASE_URL", "")
    monkeypatch.setenv("KURAL_LLM_API_KEY", "")
    s = Settings.from_env()
    assert s.llm_base_url is None
    assert s.llm_api_key is None
