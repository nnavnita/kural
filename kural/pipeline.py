"""Pipeline assembly for the kural voice agent.

Two pipelines live here:

* :func:`build_echo_pipeline` — the v0 passthrough used as a smoke test
  for the audio transport and frame plumbing.
* :func:`build_voice_pipeline` — the v0.1 STT → LLM → TTS loop.

Kept separate from :mod:`kural.server` so the pipeline graph can be
unit-tested without spinning up a real audio device or worker runner.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.pipeline.pipeline import Pipeline
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import (
    LLMContextAggregatorPair,
    LLMUserAggregatorParams,
)
from pipecat.transports.local.audio import LocalAudioTransport, LocalAudioTransportParams

from kural.config import Settings
from kural.processors import EchoProcessor
from kural.services import build_llm, build_stt, build_tts

if TYPE_CHECKING:
    from collections.abc import Sequence


def build_local_transport(settings: Settings) -> LocalAudioTransport:
    """Create a :class:`LocalAudioTransport` from the runtime settings."""
    return LocalAudioTransport(
        LocalAudioTransportParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            audio_in_sample_rate=settings.sample_rate,
            audio_out_sample_rate=settings.output_sample_rate,
        )
    )


def build_echo_pipeline(transport: LocalAudioTransport) -> Pipeline:
    """Wire ``transport.input → EchoProcessor → transport.output``."""
    return Pipeline([transport.input(), EchoProcessor(), transport.output()])


def build_voice_pipeline(
    transport: LocalAudioTransport,
    settings: Settings,
) -> tuple[Pipeline, LLMContext]:
    """Wire the v0.1 STT → LLM → TTS voice pipeline.

    Pipeline order matches the canonical Pipecat cascade:

    ``input → STT → user_aggregator → LLM → TTS → output → assistant_aggregator``

    Silero VAD lives inside ``user_aggregator`` so turn boundaries are
    detected from the captured audio without configuring VAD on the
    transport. Returns the assembled :class:`Pipeline` plus the seeded
    :class:`LLMContext` for callers that need to inspect or append to it.
    """
    context = LLMContext(messages=[{"role": "system", "content": settings.agent_prompt}])
    aggregators = LLMContextAggregatorPair(
        context,
        user_params=LLMUserAggregatorParams(vad_analyzer=SileroVADAnalyzer()),
    )

    stages: Sequence = [
        transport.input(),
        build_stt(settings),
        aggregators.user(),
        build_llm(settings),
        build_tts(settings),
        transport.output(),
        aggregators.assistant(),
    ]
    return Pipeline(list(stages)), context
