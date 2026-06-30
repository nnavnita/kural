"""Entry point for the kural agent.

Picks the pipeline based on :attr:`Settings.mode`:

* ``echo`` — v0 microphone-to-speaker passthrough. No API keys required.
* ``voice`` — v0.1 STT → LLM → TTS loop. Defaults: faster-whisper for
  STT, OpenAI-compatible LLM (set ``KURAL_LLM_BASE_URL`` to point at any
  provider), Kokoro for local TTS.

Usage::

    python -m kural.server
    # or, if installed:
    kural
"""

from __future__ import annotations

import asyncio
import sys

from loguru import logger
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.worker import PipelineWorker
from pipecat.workers.runner import WorkerRunner

from kural.config import Settings
from kural.pipeline import build_echo_pipeline, build_local_transport, build_voice_pipeline


def select_pipeline(settings: Settings) -> tuple[Pipeline, str]:
    """Return the configured pipeline plus a short ready message."""
    transport = build_local_transport(settings)
    if settings.mode == "echo":
        return (
            build_echo_pipeline(transport),
            "kural v0 echo agent ready — speak into the mic, hear yourself back. Ctrl+C to stop.",
        )
    pipeline, _context = build_voice_pipeline(transport, settings)
    return (
        pipeline,
        "kural v0.1 voice agent ready — speak into the mic, hear the reply. Ctrl+C to stop.",
    )


async def run(settings: Settings) -> None:
    """Build the configured pipeline and run it until the worker exits."""
    pipeline, ready_message = select_pipeline(settings)

    runner = WorkerRunner()
    await runner.add_workers(PipelineWorker(pipeline))

    logger.info(ready_message)
    await runner.run()


def main() -> None:  # pragma: no cover - thin runtime entry
    """CLI entry point. Configures logging and runs the selected pipeline."""
    settings = Settings.from_env()
    logger.remove()
    logger.add(sys.stderr, level=settings.log_level)

    try:
        asyncio.run(run(settings))
    except KeyboardInterrupt:
        logger.info("shutdown requested, exiting")


if __name__ == "__main__":  # pragma: no cover
    main()
