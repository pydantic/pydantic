# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class InputAudioBufferClearEvent(BaseModel):
    """Send this event to clear the audio bytes in the buffer.

    The server will
    respond with an `input_audio_buffer.cleared` event.
    """
    type: Literal['input_audio_buffer.clear']
    event_id: Optional[str] = None
