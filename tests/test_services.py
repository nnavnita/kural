"""Tests for :mod:`kural.services` registry dispatch.

These tests confirm that ``build_stt``, ``build_llm``, and ``build_tts``
look up the adapter by name in the matching registry and call its
``build`` method with the runtime settings. Adapter-internal behaviour
(which Pipecat class is constructed, with which args) is covered in
:mod:`tests.test_adapters`.
"""

from __future__ import annotations

import pytest

from kural import services
from tests.conftest import make_settings


class _FakeAdapter:
    """Adapter stub that records the settings it was asked to build with."""

    last_settings = None
    sentinel = object()

    @classmethod
    def build(cls, settings):  # type: ignore[no-untyped-def]
        cls.last_settings = settings
        return cls.sentinel


@pytest.fixture
def fake_registries(monkeypatch: pytest.MonkeyPatch) -> None:
    """Replace every provider registry with a single ``fake`` entry."""
    _FakeAdapter.last_settings = None
    monkeypatch.setattr(services, "LLM_PROVIDERS", {"fake": _FakeAdapter})
    monkeypatch.setattr(services, "STT_PROVIDERS", {"fake": _FakeAdapter})
    monkeypatch.setattr(services, "TTS_PROVIDERS", {"fake": _FakeAdapter})


def test_build_stt_dispatches_to_registered_adapter(fake_registries: None) -> None:
    settings = make_settings(stt_provider="fake")
    assert services.build_stt(settings) is _FakeAdapter.sentinel
    assert _FakeAdapter.last_settings is settings


def test_build_llm_dispatches_to_registered_adapter(fake_registries: None) -> None:
    settings = make_settings(llm_provider="fake")
    assert services.build_llm(settings) is _FakeAdapter.sentinel
    assert _FakeAdapter.last_settings is settings


def test_build_tts_dispatches_to_registered_adapter(fake_registries: None) -> None:
    settings = make_settings(tts_provider="fake")
    assert services.build_tts(settings) is _FakeAdapter.sentinel
    assert _FakeAdapter.last_settings is settings


def test_unknown_provider_raises_with_available_names(
    fake_registries: None,
) -> None:
    settings = make_settings(llm_provider="nope")
    with pytest.raises(ValueError, match="unknown LLM provider 'nope'.*fake"):
        services.build_llm(settings)


def test_unknown_provider_message_handles_empty_registry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(services, "STT_PROVIDERS", {})
    settings = make_settings(stt_provider="anything")
    with pytest.raises(ValueError, match=r"\(none registered\)"):
        services.build_stt(settings)
