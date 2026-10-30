# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class InputAudioBufferSpeechStartedEvent(BaseModel):
    """
    Sent by the server when in `server_vad` mode to indicate that speech has been
    detected in the audio buffer. This can happen any time audio is added to the
    buffer (unless speech is already detected). The client may want to use this
    event to interrupt audio playback or provide visual feedback to the user.

    The client should expect to receive a `input_audio_buffer.speech_stopped` event
    when speech stops. The `item_id` property is the ID of the user message item
    that will be created when speech stops and will also be included in the
    `input_audio_buffer.speech_stopped` event (unless the client manually commits
    the audio buffer during VAD activation).
    """
    audio_start_ms: int
    event_id: str
    item_id: str
    type: Literal['input_audio_buffer.speech_started']
