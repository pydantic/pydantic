# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class Part(BaseModel):
    """The content part that is done."""
    audio: Optional[str] = None
    text: Optional[str] = None
    transcript: Optional[str] = None
    type: Optional[Literal['text', 'audio']] = None

class ResponseContentPartDoneEvent(BaseModel):
    """
    Returned when a content part is done streaming in an assistant message item.
    Also emitted when a Response is interrupted, incomplete, or cancelled.
    """
    content_index: int
    event_id: str
    item_id: str
    output_index: int
    part: Part
    response_id: str
    type: Literal['response.content_part.done']
