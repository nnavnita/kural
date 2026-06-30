"""Shared test fixtures."""

from __future__ import annotations

import os
from collections.abc import Iterator

import pytest

from kural.config import AgentMode, Settings


@pytest.fixture
def clean_env(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Strip every ``KURAL_*`` env var so :meth:`Settings.from_env` sees defaults.

    ``python-dotenv`` is also stubbed to a no-op so a developer ``.env`` file
    cannot bleed into the test process.
    """
    for key in list(os.environ):
        if key.startswith("KURAL_"):
            monkeypatch.delenv(key, raising=False)
    monkeypatch.setattr("kural.config.load_dotenv", lambda: None)
    yield


def make_settings(
    mode: AgentMode = "echo",
    sample_rate: int = 16000,
    log_level: str = "INFO",
    llm_base_url: str | None = None,
    llm_api_key: str | None = None,
    llm_model: str = "gpt-4o-mini",
    stt_model: str = "distil-medium.en",
    tts_voice: str = "en_US-amy-medium",
    agent_prompt: str = "test prompt",
) -> Settings:
    """Build a :class:`Settings` with sensible test defaults."""
    return Settings(
        mode=mode,
        sample_rate=sample_rate,
        log_level=log_level,
        llm_base_url=llm_base_url,
        llm_api_key=llm_api_key,
        llm_model=llm_model,
        stt_model=stt_model,
        tts_voice=tts_voice,
        agent_prompt=agent_prompt,
    )
