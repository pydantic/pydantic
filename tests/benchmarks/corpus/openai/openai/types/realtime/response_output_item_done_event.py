# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel
from .conversation_item import ConversationItem

class ResponseOutputItemDoneEvent(BaseModel):
    """Returned when an Item is done streaming.

    Also emitted when a Response is
    interrupted, incomplete, or cancelled.
    """
    event_id: str
    item: ConversationItem
    output_index: int
    response_id: str
    type: Literal['response.output_item.done']
