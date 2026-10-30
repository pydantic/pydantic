# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class InputAudioBufferDtmfEventReceivedEvent(BaseModel):
    """**SIP Only:** Returned when an DTMF event is received.

    A DTMF event is a message that
    represents a telephone keypad press (0–9, *, #, A–D). The `event` property
    is the keypad that the user press. The `received_at` is the UTC Unix Timestamp
    that the server received the event.
    """
    event: str
    received_at: int
    type: Literal['input_audio_buffer.dtmf_event_received']
