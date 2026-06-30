"""Tests for :mod:`kural.pipeline`."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest
from pipecat.pipeline.pipeline import Pipeline

from kural.config import Settings
from kural.pipeline import build_echo_pipeline, build_local_transport


def test_build_local_transport_uses_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    def fake_transport(params: Any) -> MagicMock:
        captured["params"] = params
        return MagicMock(name="LocalAudioTransport")

    monkeypatch.setattr("kural.pipeline.LocalAudioTransport", fake_transport)

    settings = Settings(sample_rate=24000, log_level="INFO")
    build_local_transport(settings)

    params = captured["params"]
    assert params.audio_in_enabled is True
    assert params.audio_out_enabled is True
    assert params.audio_in_sample_rate == 24000
    assert params.audio_out_sample_rate == 24000


def test_build_echo_pipeline_wires_input_echo_output() -> None:
    transport = MagicMock()
    input_proc = MagicMock(name="input")
    output_proc = MagicMock(name="output")
    transport.input.return_value = input_proc
    transport.output.return_value = output_proc

    pipeline = build_echo_pipeline(transport)

    assert isinstance(pipeline, Pipeline)
    transport.input.assert_called_once_with()
    transport.output.assert_called_once_with()
