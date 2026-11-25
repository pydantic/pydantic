# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel
from .conversation_item import ConversationItem

class ConversationItemCreateEvent(BaseModel):
    """
    Add a new Item to the Conversation's context, including messages, function
    calls, and function call responses. This event can be used both to populate a
    "history" of the conversation and to add new items mid-stream, but has the
    current limitation that it cannot populate assistant audio messages.

    If successful, the server will emit a `conversation.item.added` event and,
    when the item is finalized, a `conversation.item.done` event. Otherwise, an
    `error` event will be sent.
    """
    item: ConversationItem
    type: Literal['conversation.item.create']
    event_id: Optional[str] = None
    previous_item_id: Optional[str] = None
