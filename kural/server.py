"""Entry point for the kural agent.

Picks the pipeline based on :attr:`Settings.mode`:

* ``echo`` — v0 microphone-to-speaker passthrough. No API keys required.
* ``voice`` — v0.1 STT → LLM → TTS loop. Defaults: faster-whisper for
  STT, OpenAI-compatible LLM (set ``KURAL_LLM_BASE_URL`` to point at any
  provider), Kokoro for local TTS.
* ``telephony`` — runs a FastAPI/uvicorn server instead of a local audio
  loop, handling inbound/outbound calls via the configured telephony
  provider (see :mod:`kural.telephony.app`). Requires
  ``KURAL_PUBLIC_BASE_URL`` and provider credentials.

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
    """Run the configured mode until it exits (Ctrl+C for local modes)."""
    if settings.mode == "telephony":
        await run_telephony(settings)
        return

    pipeline, ready_message = select_pipeline(settings)

    runner = WorkerRunner()
    await runner.add_workers(PipelineWorker(pipeline))

    logger.info(ready_message)
    await runner.run()


async def run_telephony(settings: Settings) -> None:
    """Serve the telephony FastAPI app until interrupted."""
    import uvicorn

    from kural.telephony.app import create_app

    app = create_app(settings)
    config = uvicorn.Config(
        app,
        host="0.0.0.0",  # bind all interfaces so Twilio's webhooks can reach this process
        port=settings.port,
        log_level=settings.log_level.lower(),
    )
    logger.info(
        f"kural telephony server ready on :{settings.port} "
        f"(public_base_url={settings.public_base_url})",
    )
    await uvicorn.Server(config).serve()


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
