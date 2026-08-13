"""FastAPI server for ``KURAL_MODE=telephony``.

Handles the inbound call webhook, the per-call media-stream WebSocket,
and a small REST API for outbound calls + call history. That REST API
(``/calls``, ``/calls/{sid}``, ``POST /calls/outbound``) is deliberately
provider-agnostic and persistence-backed so a future dashboard can read
it directly with no changes here.
"""

from __future__ import annotations

import asyncio
import json
import re
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from loguru import logger
from pydantic import BaseModel

from kural.adapters.registry import TELEPHONY_PROVIDERS
from kural.pipeline import build_voice_pipeline
from kural.telephony import store
from kural.telephony.registry import CallHandle, CallRegistry

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from kural.adapters.base import TelephonyAdapter
    from kural.config import Settings

_E164 = re.compile(r"^\+[1-9]\d{1,14}$")


def _resolve_adapter(settings: Settings) -> type[TelephonyAdapter]:
    try:
        return TELEPHONY_PROVIDERS[settings.telephony_provider]
    except KeyError as err:
        available = ", ".join(sorted(TELEPHONY_PROVIDERS)) or "(none registered)"
        raise ValueError(
            f"unknown telephony provider {settings.telephony_provider!r}; "
            f"registered: {available}",
        ) from err


def _media_stream_url(public_base_url: str) -> str:
    return public_base_url.replace("https://", "wss://").replace("http://", "ws://") + (
        "/telephony/media"
    )


class OutboundCallRequest(BaseModel):
    to: str
    prompt: str | None = None


def create_app(settings: Settings) -> FastAPI:
    """Build the telephony FastAPI app wired to ``settings``."""
    from pipecat.pipeline.worker import PipelineWorker
    from pipecat.transports.websocket.fastapi import (
        FastAPIWebsocketParams,
        FastAPIWebsocketTransport,
    )
    from pipecat.workers.runner import WorkerRunner

    adapter = _resolve_adapter(settings)
    calls = CallRegistry()

    @asynccontextmanager
    async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
        # WorkerRunner grabs the running event loop at construction time, so
        # it can't be built until this coroutine (already inside FastAPI's
        # loop) runs. Signal handling is left to the process-level Ctrl+C
        # handler in kural.server.main — a second handler here conflicts
        # with hosts (like uvicorn, or a test runner) that install their own.
        store.init_db(settings.db_path)
        runner = WorkerRunner(name="kural-telephony", handle_sigint=False, handle_sigterm=False)
        app.state.runner = runner
        runner_task = asyncio.create_task(runner.run(auto_end=False))
        try:
            yield
        finally:
            await runner.end()
            await runner_task

    app = FastAPI(title="kural telephony", lifespan=_lifespan)

    @app.post("/telephony/voice")
    async def voice_webhook(request: Request) -> object:
        body = await request.body()
        if not adapter.verify_webhook(request, body, settings):
            raise HTTPException(status_code=403, detail="invalid webhook signature")

        form = dict(_parse_form(body))
        call_sid = form.get("CallSid", "")
        if call_sid and store.get_call(settings.db_path, call_sid) is None:
            store.record_call_start(
                settings.db_path,
                sid=call_sid,
                direction="inbound",
                from_number=form.get("From"),
                to_number=form.get("To"),
            )

        media_url = _media_stream_url(settings.public_base_url or "")
        return adapter.handle_inbound_webhook(request, media_url)

    @app.websocket("/telephony/media")
    async def media_stream(websocket: WebSocket) -> None:
        await websocket.accept()
        try:
            await websocket.receive_text()  # "connected" event, unused
            start_raw = await websocket.receive_text()
        except WebSocketDisconnect:
            return

        start = json.loads(start_raw)["start"]
        stream_sid = start["streamSid"]
        call_sid = start["callSid"]

        serializer = adapter.build_serializer(call_sid, stream_sid, settings)
        transport = FastAPIWebsocketTransport(
            websocket=websocket,
            params=FastAPIWebsocketParams(
                audio_in_enabled=True,
                audio_out_enabled=True,
                add_wav_header=False,
                serializer=serializer,
            ),
        )
        pipeline, _context = build_voice_pipeline(transport, settings)
        worker = PipelineWorker(pipeline, name=call_sid)
        calls.add(CallHandle(sid=call_sid, direction="inbound", worker=worker))

        await websocket.app.state.runner.add_workers(worker)
        try:
            await worker.wait()
        except Exception:
            logger.exception(f"call {call_sid} ended with an error")
        finally:
            store.record_call_end(settings.db_path, call_sid)
            calls.remove(call_sid)

    @app.post("/calls/outbound")
    async def create_outbound_call(payload: OutboundCallRequest) -> dict[str, str]:
        if not _E164.match(payload.to):
            raise HTTPException(
                status_code=400,
                detail="`to` must be E.164 format, e.g. +15551234567",
            )
        if not settings.public_base_url:
            raise HTTPException(status_code=500, detail="KURAL_PUBLIC_BASE_URL is not set")

        webhook_url = f"{settings.public_base_url}/telephony/voice"
        try:
            call_sid = adapter.place_outbound_call(payload.to, settings, webhook_url)
        except Exception as err:
            raise HTTPException(status_code=502, detail=str(err)) from err

        store.record_call_start(
            settings.db_path,
            sid=call_sid,
            direction="outbound",
            from_number=settings.twilio_number,
            to_number=payload.to,
            status="dialing",
        )
        return {"sid": call_sid, "status": "dialing"}

    @app.get("/calls")
    async def list_calls() -> list[dict]:
        return [record.__dict__ for record in store.list_calls(settings.db_path)]

    @app.get("/calls/{sid}")
    async def get_call(sid: str) -> dict:
        record = store.get_call(settings.db_path, sid)
        if record is None:
            raise HTTPException(status_code=404, detail="call not found")
        return record.__dict__

    return app


def _parse_form(body: bytes) -> list[tuple[str, str]]:
    from urllib.parse import parse_qsl

    return parse_qsl(body.decode())
