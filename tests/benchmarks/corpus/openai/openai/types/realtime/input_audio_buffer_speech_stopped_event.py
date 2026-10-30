# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class InputAudioBufferSpeechStoppedEvent(BaseModel):
    """
    Returned in `server_vad` mode when the server detects the end of speech in
    the audio buffer. The server will also send an `conversation.item.created`
    event with the user message item that is created from the audio buffer.
    """
    audio_end_ms: int
    event_id: str
    item_id: str
    type: Literal['input_audio_buffer.speech_stopped']
