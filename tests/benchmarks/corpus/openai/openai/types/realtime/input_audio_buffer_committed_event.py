# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class InputAudioBufferCommittedEvent(BaseModel):
    """
    Returned when an input audio buffer is committed, either by the client or
    automatically in server VAD mode. The `item_id` property is the ID of the user
    message item that will be created, thus a `conversation.item.created` event
    will also be sent to the client.
    """
    event_id: str
    item_id: str
    type: Literal['input_audio_buffer.committed']
    previous_item_id: Optional[str] = None
