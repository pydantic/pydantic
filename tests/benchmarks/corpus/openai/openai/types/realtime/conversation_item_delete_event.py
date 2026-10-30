# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class ConversationItemDeleteEvent(BaseModel):
    """Send this event when you want to remove any item from the conversation
    history.

    The server will respond with a `conversation.item.deleted` event,
    unless the item does not exist in the conversation history, in which case the
    server will respond with an error.
    """
    item_id: str
    type: Literal['conversation.item.delete']
    event_id: Optional[str] = None
