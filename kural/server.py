"""Entry point for the v0 echo agent.

Runs a local-audio Pipecat pipeline that echoes the microphone straight
back to the speakers. See :mod:`kural.pipeline` for the pipeline graph and
:mod:`kural.processors.echo` for the frame translation logic.

Usage::

    python -m kural.server
    # or, if installed:
    kural
"""

from __future__ import annotations

import asyncio
import sys

from loguru import logger
from pipecat.pipeline.worker import PipelineWorker
from pipecat.workers.runner import WorkerRunner

from kural.config import Settings
from kural.pipeline import build_echo_pipeline, build_local_transport


async def run_echo(settings: Settings) -> None:
    """Build the echo pipeline and run it until the worker exits."""
    transport = build_local_transport(settings)
    pipeline = build_echo_pipeline(transport)

    runner = WorkerRunner()
    await runner.add_workers(PipelineWorker(pipeline))

    logger.info(
        "kural v0 echo agent ready — speak into the mic, hear yourself back. Ctrl+C to stop."
    )
    await runner.run()


def main() -> None:  # pragma: no cover - thin runtime entry
    """CLI entry point. Configures logging and runs the echo agent."""
    settings = Settings.from_env()
    logger.remove()
    logger.add(sys.stderr, level=settings.log_level)

    try:
        asyncio.run(run_echo(settings))
    except KeyboardInterrupt:
        logger.info("shutdown requested, exiting")


if __name__ == "__main__":  # pragma: no cover
    main()
