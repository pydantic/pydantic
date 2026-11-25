
# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...._models import BaseModel
from .conversation_item import ConversationItem

class ResponseOutputItemAddedEvent(BaseModel):
    event_id: str
    item: ConversationItem
    output_index: int
    response_id: str
    type: Literal['response.output_item.added']
