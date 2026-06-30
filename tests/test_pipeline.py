"""Tests for :mod:`kural.pipeline`."""

from __future__ import annotations

from typing import Any, cast
from unittest.mock import MagicMock

import pytest
from pipecat.pipeline.pipeline import Pipeline

from kural import pipeline as pipeline_mod
from kural.pipeline import build_echo_pipeline, build_local_transport, build_voice_pipeline
from tests.conftest import make_settings


def test_build_local_transport_uses_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    def fake_transport(params: Any) -> MagicMock:
        captured["params"] = params
        return MagicMock(name="LocalAudioTransport")

    monkeypatch.setattr("kural.pipeline.LocalAudioTransport", fake_transport)

    build_local_transport(make_settings(sample_rate=24000))

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


def test_build_voice_pipeline_wires_cascade(monkeypatch: pytest.MonkeyPatch) -> None:
    stt = MagicMock(name="stt")
    llm = MagicMock(name="llm")
    tts = MagicMock(name="tts")
    monkeypatch.setattr(pipeline_mod, "build_stt", MagicMock(return_value=stt))
    monkeypatch.setattr(pipeline_mod, "build_llm", MagicMock(return_value=llm))
    monkeypatch.setattr(pipeline_mod, "build_tts", MagicMock(return_value=tts))
    monkeypatch.setattr(
        pipeline_mod, "SileroVADAnalyzer", MagicMock(return_value=MagicMock(name="vad"))
    )

    user_agg = MagicMock(name="user_aggregator")
    assistant_agg = MagicMock(name="assistant_aggregator")
    pair = MagicMock(name="LLMContextAggregatorPair")
    pair.user.return_value = user_agg
    pair.assistant.return_value = assistant_agg
    monkeypatch.setattr(pipeline_mod, "LLMContextAggregatorPair", MagicMock(return_value=pair))

    captured_pipeline: dict[str, Any] = {}

    def fake_pipeline_cls(stages: list[Any]) -> MagicMock:
        captured_pipeline["stages"] = stages
        return MagicMock(name="Pipeline", spec=Pipeline)

    monkeypatch.setattr(pipeline_mod, "Pipeline", fake_pipeline_cls)

    transport = MagicMock()
    input_proc = MagicMock(name="input")
    output_proc = MagicMock(name="output")
    transport.input.return_value = input_proc
    transport.output.return_value = output_proc

    settings = make_settings(mode="voice", agent_prompt="hello there")

    _pipeline, context = build_voice_pipeline(transport, settings)

    stages = captured_pipeline["stages"]
    assert stages == [input_proc, stt, user_agg, llm, tts, output_proc, assistant_agg]
    # System prompt seeded into context
    seeded = cast(dict[str, str], context.messages[0])
    assert seeded["role"] == "system"
    assert seeded["content"] == "hello there"


def test_build_voice_pipeline_passes_settings_to_services(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stt_factory = MagicMock(return_value=MagicMock())
    llm_factory = MagicMock(return_value=MagicMock())
    tts_factory = MagicMock(return_value=MagicMock())
    monkeypatch.setattr(pipeline_mod, "build_stt", stt_factory)
    monkeypatch.setattr(pipeline_mod, "build_llm", llm_factory)
    monkeypatch.setattr(pipeline_mod, "build_tts", tts_factory)
    monkeypatch.setattr(pipeline_mod, "SileroVADAnalyzer", MagicMock())
    monkeypatch.setattr(pipeline_mod, "LLMContextAggregatorPair", MagicMock())
    monkeypatch.setattr(pipeline_mod, "Pipeline", MagicMock())

    transport = MagicMock()
    settings = make_settings(mode="voice")

    build_voice_pipeline(transport, settings)

    stt_factory.assert_called_once_with(settings)
    llm_factory.assert_called_once_with(settings)
    tts_factory.assert_called_once_with(settings)
