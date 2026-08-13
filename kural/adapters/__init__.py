"""Provider adapters for the swappable LLM/STT/TTS layers.

Each adapter wraps a single concrete Pipecat service behind a small
:mod:`kural.adapters.base` Protocol. The :mod:`kural.adapters.registry`
module maps a string provider name to its adapter class so the rest of
the codebase can select a backend purely from configuration.

Adding a provider requires only a new adapter class and a registry
entry — :mod:`kural.services` and :mod:`kural.pipeline` are unaware of
which concrete implementation is wired in.
"""

from kural.adapters.base import LLMAdapter, STTAdapter, TelephonyAdapter, TTSAdapter
from kural.adapters.registry import (
    LLM_PROVIDERS,
    STT_PROVIDERS,
    TELEPHONY_PROVIDERS,
    TTS_PROVIDERS,
)

__all__ = [
    "LLM_PROVIDERS",
    "LLMAdapter",
    "STTAdapter",
    "STT_PROVIDERS",
    "TTSAdapter",
    "TTS_PROVIDERS",
    "TelephonyAdapter",
    "TELEPHONY_PROVIDERS",
]
