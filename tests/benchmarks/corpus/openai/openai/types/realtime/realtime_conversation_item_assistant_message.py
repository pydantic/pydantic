# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Optional
from typing_extensions import Literal
from ..._models import BaseModel

class Content(BaseModel):
    audio: Optional[str] = None
    text: Optional[str] = None
    transcript: Optional[str] = None
    type: Optional[Literal['output_text', 'output_audio']] = None

class RealtimeConversationItemAssistantMessage(BaseModel):
    """An assistant message item in a Realtime conversation."""
    content: List[Content]
    role: Literal['assistant']
    type: Literal['message']
    id: Optional[str] = None
    object: Optional[Literal['realtime.item']] = None
    status: Optional[Literal['completed', 'incomplete', 'in_progress']] = None
