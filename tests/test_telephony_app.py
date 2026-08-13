"""Tests for the telephony FastAPI app.

The telephony provider is swapped for a ``MagicMock`` registered under a
throwaway ``"fake"`` key in :data:`kural.telephony.app.TELEPHONY_PROVIDERS`
(same registry-substitution technique as :mod:`tests.test_adapters`), so
these tests exercise the HTTP/webhook/REST wiring without touching the
real Twilio SDK. The WebSocket media-stream path (which builds a real
voice pipeline) is covered separately in ``test_media_stream_*``, with
Pipecat's worker/transport classes patched at their source module.
"""

from __future__ import annotations

import json
import time
from collections.abc import Iterator
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import Response
from fastapi.testclient import TestClient
from pipecat.serializers.base_serializer import FrameSerializer

from kural.telephony import app as app_module
from kural.telephony import store
from tests.conftest import make_settings


@pytest.fixture
def fake_adapter(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    adapter = MagicMock(name="FakeTelephonyAdapter")
    adapter.verify_webhook.return_value = True
    adapter.handle_inbound_webhook.return_value = Response(
        content="<Response><Connect/></Response>", media_type="application/xml"
    )
    adapter.place_outbound_call.return_value = "CA-OUT-1"
    monkeypatch.setitem(app_module.TELEPHONY_PROVIDERS, "fake", adapter)
    return adapter


@pytest.fixture
def client(tmp_path: Path, fake_adapter: MagicMock) -> Iterator[TestClient]:
    settings = make_settings(
        mode="telephony",
        telephony_provider="fake",
        public_base_url="https://example.ngrok.app",
        db_path=str(tmp_path / "calls.db"),
    )
    app = app_module.create_app(settings)
    with TestClient(app) as test_client:
        test_client.app_settings = settings  # type: ignore[attr-defined]
        yield test_client


def _twilio_form(**overrides: str) -> dict[str, str]:
    form = {"CallSid": "CA1", "From": "+15551234567", "To": "+15557654321"}
    form.update(overrides)
    return form


# --- POST /telephony/voice --------------------------------------------------


def test_voice_webhook_accepts_valid_signature_and_logs_call(
    client: TestClient, fake_adapter: MagicMock
) -> None:
    response = client.post("/telephony/voice", data=_twilio_form())

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/xml")
    fake_adapter.handle_inbound_webhook.assert_called_once()
    media_url = fake_adapter.handle_inbound_webhook.call_args.args[1]
    assert media_url == "wss://example.ngrok.app/telephony/media"

    record = store.get_call(client.app_settings.db_path, "CA1")  # type: ignore[attr-defined]
    assert record is not None
    assert record.direction == "inbound"
    assert record.from_number == "+15551234567"
    assert record.to_number == "+15557654321"


def test_voice_webhook_rejects_bad_signature(client: TestClient, fake_adapter: MagicMock) -> None:
    fake_adapter.verify_webhook.return_value = False

    response = client.post("/telephony/voice", data=_twilio_form())

    assert response.status_code == 403
    fake_adapter.handle_inbound_webhook.assert_not_called()


def test_voice_webhook_does_not_duplicate_outbound_call_row(
    client: TestClient, fake_adapter: MagicMock
) -> None:
    # simulate an outbound call already logged with status "dialing"
    store.record_call_start(
        client.app_settings.db_path,  # type: ignore[attr-defined]
        sid="CA1",
        direction="outbound",
        from_number="+15557654321",
        to_number="+15551234567",
        status="dialing",
    )

    client.post("/telephony/voice", data=_twilio_form())

    record = store.get_call(client.app_settings.db_path, "CA1")  # type: ignore[attr-defined]
    assert record is not None
    assert record.direction == "outbound"  # untouched, not overwritten to "inbound"


# --- POST /calls/outbound ---------------------------------------------------


def test_outbound_call_rejects_bad_e164(client: TestClient) -> None:
    response = client.post("/calls/outbound", json={"to": "555-1234"})
    assert response.status_code == 400


def test_outbound_call_places_call_and_logs_it(client: TestClient, fake_adapter: MagicMock) -> None:
    response = client.post("/calls/outbound", json={"to": "+15551234567"})

    assert response.status_code == 200
    assert response.json() == {"sid": "CA-OUT-1", "status": "dialing"}
    fake_adapter.place_outbound_call.assert_called_once_with(
        "+15551234567",
        client.app_settings,  # type: ignore[attr-defined]
        "https://example.ngrok.app/telephony/voice",
    )

    record = store.get_call(client.app_settings.db_path, "CA-OUT-1")  # type: ignore[attr-defined]
    assert record is not None
    assert record.direction == "outbound"
    assert record.status == "dialing"


def test_outbound_call_provider_error_returns_502(
    client: TestClient, fake_adapter: MagicMock
) -> None:
    fake_adapter.place_outbound_call.side_effect = RuntimeError("twilio boom")

    response = client.post("/calls/outbound", json={"to": "+15551234567"})

    assert response.status_code == 502


# --- GET /calls, GET /calls/{sid} -------------------------------------------


def test_list_and_get_calls(client: TestClient) -> None:
    client.post("/telephony/voice", data=_twilio_form())

    listed = client.get("/calls").json()
    assert len(listed) == 1
    assert listed[0]["sid"] == "CA1"

    fetched = client.get("/calls/CA1")
    assert fetched.status_code == 200
    assert fetched.json()["sid"] == "CA1"

    missing = client.get("/calls/does-not-exist")
    assert missing.status_code == 404


# --- WS /telephony/media -----------------------------------------------------


def test_media_stream_runs_pipeline_and_records_call_end(
    tmp_path: Path, fake_adapter: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    # WorkerRunner's real add_workers() drives a whole internal attach/bus/
    # registry lifecycle on the worker it's given — not worth re-implementing
    # against a mock. Patch the runner itself, same technique test_server.py
    # uses for the local WorkerRunner.
    fake_serializer = MagicMock(name="TwilioFrameSerializer", spec=FrameSerializer)
    fake_adapter.build_serializer.return_value = fake_serializer

    monkeypatch.setattr(
        "pipecat.transports.websocket.fastapi.FastAPIWebsocketTransport", MagicMock()
    )
    monkeypatch.setattr(
        "kural.telephony.app.build_voice_pipeline",
        MagicMock(return_value=(MagicMock(name="Pipeline"), MagicMock())),
    )

    fake_worker = MagicMock(name="PipelineWorker")
    fake_worker.wait = AsyncMock()
    monkeypatch.setattr(
        "pipecat.pipeline.worker.PipelineWorker", MagicMock(return_value=fake_worker)
    )

    fake_runner = MagicMock(name="WorkerRunner")
    fake_runner.run = AsyncMock()
    fake_runner.add_workers = AsyncMock()
    fake_runner.end = AsyncMock()
    monkeypatch.setattr("pipecat.workers.runner.WorkerRunner", MagicMock(return_value=fake_runner))

    settings = make_settings(
        mode="telephony",
        telephony_provider="fake",
        public_base_url="https://example.ngrok.app",
        db_path=str(tmp_path / "calls.db"),
    )
    app = app_module.create_app(settings)

    with TestClient(app) as client:
        # Real calls always hit the webhook first, which is what inserts
        # the call row; open the WS the same way instead of pre-seeding
        # the row directly.
        client.post("/telephony/voice", data=_twilio_form(CallSid="CA-WS-1"))

        with client.websocket_connect("/telephony/media") as ws:
            ws.send_text(json.dumps({"event": "connected"}))
            ws.send_text(
                json.dumps({"event": "start", "start": {"streamSid": "MZ1", "callSid": "CA-WS-1"}})
            )
            # The server-side handler runs on a background thread with no
            # synchronization point exposed back to the test client, so poll
            # (bounded) for it to reach the finally block instead of assuming
            # send_text() implies the handler has finished.
            for _ in range(50):
                record = store.get_call(settings.db_path, "CA-WS-1")
                if record is not None and record.status == "completed":
                    break
                time.sleep(0.02)

    fake_worker.wait.assert_awaited_once()
    fake_runner.add_workers.assert_awaited_once_with(fake_worker)
    record = store.get_call(settings.db_path, "CA-WS-1")
    assert record is not None
    assert record.status == "completed"
