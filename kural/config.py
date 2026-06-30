"""Runtime configuration loaded from environment variables.

All settings are read once at startup via :meth:`Settings.from_env`, which
also loads a ``.env`` file (if present) using :mod:`python-dotenv`.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    """Immutable container for the values the runtime needs.

    Attributes:
        sample_rate: Sample rate (Hz) used by the local audio transport.
            16 kHz is the Pipecat default and matches Whisper/Silero.
        log_level: loguru log level (``DEBUG``, ``INFO``, ``WARNING``, ...).
    """

    sample_rate: int
    log_level: str

    @classmethod
    def from_env(cls) -> Settings:
        """Construct a :class:`Settings` from environment variables.

        Loads ``.env`` if present. Recognised variables:

        - ``KURAL_SAMPLE_RATE`` (int, default ``16000``)
        - ``KURAL_LOG_LEVEL`` (str, default ``INFO``; upper-cased)
        """
        load_dotenv()
        return cls(
            sample_rate=int(os.getenv("KURAL_SAMPLE_RATE", "16000")),
            log_level=os.getenv("KURAL_LOG_LEVEL", "INFO").upper(),
        )
