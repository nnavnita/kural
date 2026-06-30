"""Pipeline assembly for the v0 echo agent.

Kept separate from :mod:`kural.server` so the pipeline graph can be
unit-tested without spinning up a real audio device or worker runner.
"""

from __future__ import annotations

from pipecat.pipeline.pipeline import Pipeline
from pipecat.transports.local.audio import LocalAudioTransport, LocalAudioTransportParams

from kural.config import Settings
from kural.processors import EchoProcessor


def build_local_transport(settings: Settings) -> LocalAudioTransport:
    """Create a :class:`LocalAudioTransport` from the runtime settings."""
    return LocalAudioTransport(
        LocalAudioTransportParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            audio_in_sample_rate=settings.sample_rate,
            audio_out_sample_rate=settings.sample_rate,
        )
    )


def build_echo_pipeline(transport: LocalAudioTransport) -> Pipeline:
    """Wire ``transport.input → EchoProcessor → transport.output``."""
    return Pipeline([transport.input(), EchoProcessor(), transport.output()])
