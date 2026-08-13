"""Tests for the Twilio telephony adapter.

The Twilio SDK classes (``RequestValidator``, ``Client``,
``TwilioFrameSerializer``) are imported lazily inside the adapter's
methods, so tests patch them at their source module path — same
technique :mod:`tests.test_adapters` uses for Pipecat services.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from kural.adapters import TELEPHONY_PROVIDERS, TelephonyAdapter
from kural.adapters.twilio_tel import TwilioTelephonyAdapter
from tests.conftest import make_settings


def test_twilio_adapter_satisfies_telephony_protocol() -> None:
    assert isinstance(TwilioTelephonyAdapter, TelephonyAdapter)


def test_default_telephony_provider_is_registered() -> None:
    assert TELEPHONY_PROVIDERS["twilio"] is TwilioTelephonyAdapter


# --- verify_webhook --------------------------------------------------------


def test_verify_webhook_without_auth_token_rejects() -> None:
    settings = make_settings(twilio_auth_token=None)
    result = TwilioTelephonyAdapter.verify_webhook(MagicMock(), b"", settings)
    assert result is False


def test_verify_webhook_delegates_to_request_validator(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    validator = MagicMock()
    validator.validate.return_value = True
    validator_cls = MagicMock(return_value=validator)
    monkeypatch.setattr("twilio.request_validator.RequestValidator", validator_cls)

    settings = make_settings(twilio_auth_token="secret")
    request = MagicMock()
    request.headers = {"X-Twilio-Signature": "sig123"}
    request.url = "https://example.com/telephony/voice"

    result = TwilioTelephonyAdapter.verify_webhook(
        request, b"CallSid=CA123&From=%2B1555", settings
    )

    assert result is True
    validator_cls.assert_called_once_with("secret")
    validator.validate.assert_called_once_with(
        "https://example.com/telephony/voice",
        {"CallSid": "CA123", "From": "+1555"},
        "sig123",
    )


def test_verify_webhook_rejects_bad_signature(monkeypatch: pytest.MonkeyPatch) -> None:
    validator = MagicMock()
    validator.validate.return_value = False
    monkeypatch.setattr(
        "twilio.request_validator.RequestValidator", MagicMock(return_value=validator)
    )

    settings = make_settings(twilio_auth_token="secret")
    request = MagicMock()
    request.headers = {"X-Twilio-Signature": "bad"}
    request.url = "https://example.com/telephony/voice"

    assert TwilioTelephonyAdapter.verify_webhook(request, b"", settings) is False


# --- handle_inbound_webhook -------------------------------------------------


def test_handle_inbound_webhook_returns_twiml_stream() -> None:
    response = TwilioTelephonyAdapter.handle_inbound_webhook(
        MagicMock(), "wss://example.com/telephony/media"
    )

    assert response.media_type == "application/xml"
    body = bytes(response.body).decode()
    assert "<Connect>" in body
    assert "wss://example.com/telephony/media" in body


# --- build_serializer --------------------------------------------------------


def test_build_serializer_passes_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    serializer_cls = MagicMock()
    monkeypatch.setattr("pipecat.serializers.twilio.TwilioFrameSerializer", serializer_cls)

    settings = make_settings(twilio_account_sid="AC1", twilio_auth_token="secret")
    result = TwilioTelephonyAdapter.build_serializer("CA1", "MZ1", settings)

    serializer_cls.assert_called_once_with(
        stream_sid="MZ1", call_sid="CA1", account_sid="AC1", auth_token="secret"
    )
    assert result is serializer_cls.return_value


# --- place_outbound_call -----------------------------------------------------


def test_place_outbound_call_uses_twilio_client(monkeypatch: pytest.MonkeyPatch) -> None:
    call = MagicMock()
    call.sid = "CA999"
    client = MagicMock()
    client.calls.create.return_value = call
    client_cls = MagicMock(return_value=client)
    monkeypatch.setattr("twilio.rest.Client", client_cls)

    settings = make_settings(
        twilio_account_sid="AC1", twilio_auth_token="secret", twilio_number="+15550000000"
    )
    sid = TwilioTelephonyAdapter.place_outbound_call(
        "+15551234567", settings, "https://example.com/telephony/voice"
    )

    client_cls.assert_called_once_with("AC1", "secret")
    client.calls.create.assert_called_once_with(
        to="+15551234567", from_="+15550000000", url="https://example.com/telephony/voice"
    )
    assert sid == "CA999"
