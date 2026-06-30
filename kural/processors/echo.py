"""Echo processor: rewraps captured mic audio as playback audio.

Pipecat's :class:`LocalAudioTransport` emits ``InputAudioRawFrame`` from the
microphone, but the same transport's output sink only plays
``OutputAudioRawFrame``. The two are structurally identical (audio bytes +
sample rate + channels) but typed distinctly so the pipeline can tell
captured audio apart from synthesised audio.

The v0 echo agent needs raw mic audio to play straight back through the
speakers, so we sit a tiny translator processor in between input and output
that rewraps every ``InputAudioRawFrame`` as ``OutputAudioRawFrame`` and
leaves every other frame untouched.
"""

from __future__ import annotations

from pipecat.frames.frames import Frame, InputAudioRawFrame, OutputAudioRawFrame
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor


class EchoProcessor(FrameProcessor):
    """Translate ``InputAudioRawFrame`` to ``OutputAudioRawFrame`` in place."""

    async def process_frame(self, frame: Frame, direction: FrameDirection) -> None:
        await super().process_frame(frame, direction)
        if isinstance(frame, InputAudioRawFrame):
            await self.push_frame(
                OutputAudioRawFrame(
                    audio=frame.audio,
                    sample_rate=frame.sample_rate,
                    num_channels=frame.num_channels,
                )
            )
        else:
            await self.push_frame(frame, direction)
