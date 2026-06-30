"""Tests for :func:`kural.server.run_echo`.

The runtime hooks (``WorkerRunner``, ``PipelineWorker``, the audio
transport) are mocked out so the assembly logic can be verified without
opening real audio devices or scheduling worker tasks.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from kural import server
from kural.config import Settings


@pytest.fixture
def fake_runtime(monkeypatch: pytest.MonkeyPatch) -> dict[str, MagicMock]:
    runner = MagicMock(name="WorkerRunner")
    runner.add_workers = AsyncMock()
    runner.run = AsyncMock()
    runner_cls = MagicMock(return_value=runner)

    worker_cls = MagicMock(name="PipelineWorker")
    transport = MagicMock(name="LocalAudioTransport")
    transport_factory = MagicMock(return_value=transport)
    pipeline = MagicMock(name="Pipeline")
    pipeline_factory = MagicMock(return_value=pipeline)

    monkeypatch.setattr(server, "WorkerRunner", runner_cls)
    monkeypatch.setattr(server, "PipelineWorker", worker_cls)
    monkeypatch.setattr(server, "build_local_transport", transport_factory)
    monkeypatch.setattr(server, "build_echo_pipeline", pipeline_factory)

    return {
        "runner": runner,
        "runner_cls": runner_cls,
        "worker_cls": worker_cls,
        "transport": transport,
        "transport_factory": transport_factory,
        "pipeline": pipeline,
        "pipeline_factory": pipeline_factory,
    }


async def test_run_echo_builds_and_runs_pipeline(
    fake_runtime: dict[str, MagicMock],
) -> None:
    settings = Settings(sample_rate=16000, log_level="INFO")

    await server.run_echo(settings)

    fake_runtime["transport_factory"].assert_called_once_with(settings)
    fake_runtime["pipeline_factory"].assert_called_once_with(fake_runtime["transport"])
    fake_runtime["worker_cls"].assert_called_once_with(fake_runtime["pipeline"])
    fake_runtime["runner"].add_workers.assert_awaited_once()
    fake_runtime["runner"].run.assert_awaited_once()
