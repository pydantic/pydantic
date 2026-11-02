# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class InputAudioBufferClearedEvent(BaseModel):
    """
    Returned when the input audio buffer is cleared by the client with a
    `input_audio_buffer.clear` event.
    """
    event_id: str
    type: Literal['input_audio_buffer.cleared']
