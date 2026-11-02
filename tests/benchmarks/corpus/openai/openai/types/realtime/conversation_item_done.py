# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel
from .conversation_item import ConversationItem

class ConversationItemDone(BaseModel):
    """Returned when a conversation item is finalized.

    The event will include the full content of the Item except for audio data, which can be retrieved separately with a `conversation.item.retrieve` event if needed.
    """
    event_id: str
    item: ConversationItem
    type: Literal['conversation.item.done']
    previous_item_id: Optional[str] = None
