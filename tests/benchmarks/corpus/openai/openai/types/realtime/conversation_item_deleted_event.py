# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class ConversationItemDeletedEvent(BaseModel):
    """
    Returned when an item in the conversation is deleted by the client with a
    `conversation.item.delete` event. This event is used to synchronize the
    server's understanding of the conversation history with the client's view.
    """
    event_id: str
    item_id: str
    type: Literal['conversation.item.deleted']
