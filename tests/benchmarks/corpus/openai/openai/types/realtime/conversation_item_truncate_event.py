# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class ConversationItemTruncateEvent(BaseModel):
    """Send this event to truncate a previous assistant message’s audio.

    The server
    will produce audio faster than realtime, so this event is useful when the user
    interrupts to truncate audio that has already been sent to the client but not
    yet played. This will synchronize the server's understanding of the audio with
    the client's playback.

    Truncating audio will delete the server-side text transcript to ensure there
    is not text in the context that hasn't been heard by the user.

    If successful, the server will respond with a `conversation.item.truncated`
    event.
    """
    audio_end_ms: int
    content_index: int
    item_id: str
    type: Literal['conversation.item.truncate']
    event_id: Optional[str] = None
