"""Twilio telephony adapter.

Bridges Twilio Voice (inbound webhook + Media Streams WebSocket, outbound
REST dial) to a Pipecat pipeline via :class:`~pipecat.serializers.twilio.
TwilioFrameSerializer`. First implementation of :class:`~kural.adapters.
base.TelephonyAdapter` — other providers (Telnyx, Plivo, ...) plug in the
same way, since Pipecat ships a matching serializer for each.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from fastapi import Request, Response
    from pipecat.serializers.twilio import TwilioFrameSerializer

    from kural.config import Settings


class TwilioTelephonyAdapter:
    """TelephonyAdapter backed by Twilio Voice + Media Streams."""

    name: ClassVar[str] = "twilio"

    @staticmethod
    def verify_webhook(request: Request, body: bytes, settings: Settings) -> bool:
        from twilio.request_validator import RequestValidator

        if not settings.twilio_auth_token:
            return False

        signature = request.headers.get("X-Twilio-Signature", "")
        validator = RequestValidator(settings.twilio_auth_token)
        form = dict(_parse_form(body))
        return validator.validate(str(request.url), form, signature)

    @staticmethod
    def handle_inbound_webhook(request: Request, media_stream_url: str) -> Response:
        from fastapi import Response
        from twilio.twiml.voice_response import Connect, VoiceResponse

        twiml = VoiceResponse()
        connect = Connect()
        connect.stream(url=media_stream_url)
        twiml.append(connect)
        return Response(content=str(twiml), media_type="application/xml")

    @staticmethod
    def build_serializer(
        call_sid: str, stream_sid: str, settings: Settings
    ) -> TwilioFrameSerializer:
        from pipecat.serializers.twilio import TwilioFrameSerializer

        return TwilioFrameSerializer(
            stream_sid=stream_sid,
            call_sid=call_sid,
            account_sid=settings.twilio_account_sid,
            auth_token=settings.twilio_auth_token,
        )

    @staticmethod
    def place_outbound_call(to: str, settings: Settings, webhook_url: str) -> str:
        from twilio.rest import Client

        client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
        call = client.calls.create(to=to, from_=settings.twilio_number, url=webhook_url)
        return call.sid


def _parse_form(body: bytes) -> list[tuple[str, str]]:
    from urllib.parse import parse_qsl

    return parse_qsl(body.decode())
