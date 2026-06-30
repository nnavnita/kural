"""Shared test fixtures."""

from __future__ import annotations

import os
from collections.abc import Iterator

import pytest


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
