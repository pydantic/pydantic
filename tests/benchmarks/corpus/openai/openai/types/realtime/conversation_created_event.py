# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class Conversation(BaseModel):
    """The conversation resource."""
    id: Optional[str] = None
    object: Optional[Literal['realtime.conversation']] = None

class ConversationCreatedEvent(BaseModel):
    """Returned when a conversation is created. Emitted right after session creation."""
    conversation: Conversation
    event_id: str
    type: Literal['conversation.created']
