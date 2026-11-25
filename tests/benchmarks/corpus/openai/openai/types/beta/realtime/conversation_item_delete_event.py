
# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ...._models import BaseModel

class ConversationItemDeleteEvent(BaseModel):
    item_id: str
    type: Literal['conversation.item.delete']
    event_id: Optional[str] = None
