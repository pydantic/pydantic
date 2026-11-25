# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel
from .conversation_item import ConversationItem

class ConversationItemAdded(BaseModel):
    """Sent by the server when an Item is added to the default Conversation.

    This can happen in several cases:
    - When the client sends a `conversation.item.create` event.
    - When the input audio buffer is committed. In this case the item will be a user message containing the audio from the buffer.
    - When the model is generating a Response. In this case the `conversation.item.added` event will be sent when the model starts generating a specific Item, and thus it will not yet have any content (and `status` will be `in_progress`).

    The event will include the full content of the Item (except when model is generating a Response) except for audio data, which can be retrieved separately with a `conversation.item.retrieve` event if necessary.
    """
    event_id: str
    item: ConversationItem
    type: Literal['conversation.item.added']
    previous_item_id: Optional[str] = None
