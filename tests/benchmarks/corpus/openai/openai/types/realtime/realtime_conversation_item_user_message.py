# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Optional
from typing_extensions import Literal
from ..._models import BaseModel

class Content(BaseModel):
    audio: Optional[str] = None
    detail: Optional[Literal['auto', 'low', 'high']] = None
    image_url: Optional[str] = None
    text: Optional[str] = None
    transcript: Optional[str] = None
    type: Optional[Literal['input_text', 'input_audio', 'input_image']] = None

class RealtimeConversationItemUserMessage(BaseModel):
    """A user message item in a Realtime conversation."""
    content: List[Content]
    role: Literal['user']
    type: Literal['message']
    id: Optional[str] = None
    object: Optional[Literal['realtime.item']] = None
    status: Optional[Literal['completed', 'incomplete', 'in_progress']] = None
