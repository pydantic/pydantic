
# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ...._models import BaseModel

class ConversationItemTruncateEvent(BaseModel):
    audio_end_ms: int
    content_index: int
    item_id: str
    type: Literal['conversation.item.truncate']
    event_id: Optional[str] = None
