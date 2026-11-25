# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class ConversationItemRetrieveEvent(BaseModel):
    """
    Send this event when you want to retrieve the server's representation of a specific item in the conversation history. This is useful, for example, to inspect user audio after noise cancellation and VAD.
    The server will respond with a `conversation.item.retrieved` event,
    unless the item does not exist in the conversation history, in which case the
    server will respond with an error.
    """
    item_id: str
    type: Literal['conversation.item.retrieve']
    event_id: Optional[str] = None
