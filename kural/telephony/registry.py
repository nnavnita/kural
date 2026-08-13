"""In-memory registry of active calls.

Tracks which calls are currently running so the REST API can look them
up. Call history that outlives a single process lives in
:mod:`kural.telephony.store` (SQLite) — this registry is purely runtime
state, cleared on process restart.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pipecat.pipeline.worker import PipelineWorker


@dataclass
class CallHandle:
    """One active call: its SID, direction, and the worker running it."""

    sid: str
    direction: str
    worker: PipelineWorker | Any


class CallRegistry:
    """Maps call SID to :class:`CallHandle` for the calls currently in progress."""

    def __init__(self) -> None:
        self._calls: dict[str, CallHandle] = {}

    def add(self, handle: CallHandle) -> None:
        self._calls[handle.sid] = handle

    def get(self, sid: str) -> CallHandle | None:
        return self._calls.get(sid)

    def remove(self, sid: str) -> None:
        self._calls.pop(sid, None)

    def list_active(self) -> list[CallHandle]:
        return list(self._calls.values())

    def __len__(self) -> int:
        return len(self._calls)
