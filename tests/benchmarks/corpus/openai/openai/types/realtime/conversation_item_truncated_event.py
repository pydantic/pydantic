# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class ConversationItemTruncatedEvent(BaseModel):
    """
    Returned when an earlier assistant audio message item is truncated by the
    client with a `conversation.item.truncate` event. This event is used to
    synchronize the server's understanding of the audio with the client's playback.

    This action will truncate the audio and remove the server-side text transcript
    to ensure there is no text in the context that hasn't been heard by the user.
    """
    audio_end_ms: int
    content_index: int
    event_id: str
    item_id: str
    type: Literal['conversation.item.truncated']
