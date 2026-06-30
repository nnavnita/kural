"""Tests for :func:`kural.server.run` and pipeline selection.

The runtime hooks (``WorkerRunner``, ``PipelineWorker``, the audio
transport) are mocked out so the assembly logic can be verified without
opening real audio devices or scheduling worker tasks.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from kural import server
from tests.conftest import make_settings


@pytest.fixture
def fake_runtime(monkeypatch: pytest.MonkeyPatch) -> dict[str, MagicMock]:
    runner = MagicMock(name="WorkerRunner")
    runner.add_workers = AsyncMock()
    runner.run = AsyncMock()
    runner_cls = MagicMock(return_value=runner)

    worker_cls = MagicMock(name="PipelineWorker")
    transport = MagicMock(name="LocalAudioTransport")
    transport_factory = MagicMock(return_value=transport)
    echo_pipeline = MagicMock(name="EchoPipeline")
    echo_factory = MagicMock(return_value=echo_pipeline)
    voice_pipeline = MagicMock(name="VoicePipeline")
    voice_context = MagicMock(name="LLMContext")
    voice_factory = MagicMock(return_value=(voice_pipeline, voice_context))

    monkeypatch.setattr(server, "WorkerRunner", runner_cls)
    monkeypatch.setattr(server, "PipelineWorker", worker_cls)
    monkeypatch.setattr(server, "build_local_transport", transport_factory)
    monkeypatch.setattr(server, "build_echo_pipeline", echo_factory)
    monkeypatch.setattr(server, "build_voice_pipeline", voice_factory)

    return {
        "runner": runner,
        "runner_cls": runner_cls,
        "worker_cls": worker_cls,
        "transport": transport,
        "transport_factory": transport_factory,
        "echo_pipeline": echo_pipeline,
        "echo_factory": echo_factory,
        "voice_pipeline": voice_pipeline,
        "voice_factory": voice_factory,
    }


def test_select_pipeline_echo_mode(fake_runtime: dict[str, MagicMock]) -> None:
    settings = make_settings(mode="echo")

    pipeline, message = server.select_pipeline(settings)

    assert pipeline is fake_runtime["echo_pipeline"]
    fake_runtime["echo_factory"].assert_called_once_with(fake_runtime["transport"])
    fake_runtime["voice_factory"].assert_not_called()
    assert "echo" in message.lower()


def test_select_pipeline_voice_mode(fake_runtime: dict[str, MagicMock]) -> None:
    settings = make_settings(mode="voice")

    pipeline, message = server.select_pipeline(settings)

    assert pipeline is fake_runtime["voice_pipeline"]
    fake_runtime["voice_factory"].assert_called_once_with(fake_runtime["transport"], settings)
    fake_runtime["echo_factory"].assert_not_called()
    assert "voice" in message.lower()


async def test_run_builds_and_runs_voice_pipeline(
    fake_runtime: dict[str, MagicMock],
) -> None:
    settings = make_settings(mode="voice")

    await server.run(settings)

    fake_runtime["transport_factory"].assert_called_once_with(settings)
    fake_runtime["voice_factory"].assert_called_once_with(fake_runtime["transport"], settings)
    fake_runtime["worker_cls"].assert_called_once_with(fake_runtime["voice_pipeline"])
    fake_runtime["runner"].add_workers.assert_awaited_once()
    fake_runtime["runner"].run.assert_awaited_once()


async def test_run_builds_and_runs_echo_pipeline(
    fake_runtime: dict[str, MagicMock],
) -> None:
    settings = make_settings(mode="echo")

    await server.run(settings)

    fake_runtime["echo_factory"].assert_called_once_with(fake_runtime["transport"])
    fake_runtime["worker_cls"].assert_called_once_with(fake_runtime["echo_pipeline"])
    fake_runtime["runner"].run.assert_awaited_once()
