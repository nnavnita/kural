"""Tests for :mod:`kural.config`."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from kural.config import Settings


def test_defaults(clean_env: None) -> None:
    s = Settings.from_env()
    assert s.sample_rate == 16000
    assert s.log_level == "INFO"


def test_env_override(clean_env: None, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KURAL_SAMPLE_RATE", "24000")
    monkeypatch.setenv("KURAL_LOG_LEVEL", "debug")
    s = Settings.from_env()
    assert s.sample_rate == 24000
    assert s.log_level == "DEBUG"


def test_settings_is_frozen() -> None:
    s = Settings(sample_rate=16000, log_level="INFO")
    with pytest.raises(FrozenInstanceError):
        s.sample_rate = 48000  # type: ignore[misc]


def test_invalid_sample_rate_raises(clean_env: None, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KURAL_SAMPLE_RATE", "not-a-number")
    with pytest.raises(ValueError):
        Settings.from_env()
