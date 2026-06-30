"""Tests for :class:`kural.processors.echo.EchoProcessor`."""

from __future__ import annotations

import pytest
from pipecat.frames.frames import (
    Frame,
    InputAudioRawFrame,
    OutputAudioRawFrame,
    TextFrame,
)
from pipecat.processors.frame_processor import FrameDirection

from kural.processors.echo import EchoProcessor


class _RecordingEcho(EchoProcessor):
    """EchoProcessor with ``push_frame`` captured for assertions.

    Skipping :meth:`FrameProcessor.push_frame` avoids needing a fully linked
    pipeline; the only thing under test here is what the processor *emits*.
    """

    def __init__(self) -> None:
        super().__init__()
        self.emitted: list[tuple[Frame, FrameDirection]] = []

    async def push_frame(
        self, frame: Frame, direction: FrameDirection = FrameDirection.DOWNSTREAM
    ) -> None:
        self.emitted.append((frame, direction))


@pytest.fixture
def proc() -> _RecordingEcho:
    return _RecordingEcho()


async def test_input_audio_is_rewrapped_as_output(proc: _RecordingEcho) -> None:
    audio = b"\x01\x02\x03\x04"
    frame = InputAudioRawFrame(audio=audio, sample_rate=16000, num_channels=1)

    await proc.process_frame(frame, FrameDirection.DOWNSTREAM)

    assert len(proc.emitted) == 1
    emitted, direction = proc.emitted[0]
    assert isinstance(emitted, OutputAudioRawFrame)
    assert emitted.audio == audio
    assert emitted.sample_rate == 16000
    assert emitted.num_channels == 1
    # OutputAudioRawFrame always flows downstream by default
    assert direction == FrameDirection.DOWNSTREAM


async def test_non_audio_frame_passes_through_unchanged(proc: _RecordingEcho) -> None:
    frame = TextFrame(text="hello")

    await proc.process_frame(frame, FrameDirection.UPSTREAM)

    assert proc.emitted == [(frame, FrameDirection.UPSTREAM)]


async def test_input_audio_preserves_multichannel_metadata(
    proc: _RecordingEcho,
) -> None:
    frame = InputAudioRawFrame(audio=b"\x00\x00", sample_rate=48000, num_channels=2)

    await proc.process_frame(frame, FrameDirection.DOWNSTREAM)

    emitted, _ = proc.emitted[0]
    assert isinstance(emitted, OutputAudioRawFrame)
    assert emitted.sample_rate == 48000
    assert emitted.num_channels == 2
