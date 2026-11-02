
# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ...._models import BaseModel

class Conversation(BaseModel):
    id: Optional[str] = None
    object: Optional[Literal['realtime.conversation']] = None

class ConversationCreatedEvent(BaseModel):
    conversation: Conversation
    event_id: str
    type: Literal['conversation.created']
