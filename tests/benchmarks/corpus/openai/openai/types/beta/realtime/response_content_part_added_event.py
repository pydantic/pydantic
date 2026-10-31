
# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ...._models import BaseModel

class Part(BaseModel):
    audio: Optional[str] = None
    text: Optional[str] = None
    transcript: Optional[str] = None
    type: Optional[Literal['text', 'audio']] = None

class ResponseContentPartAddedEvent(BaseModel):
    content_index: int
    event_id: str
    item_id: str
    output_index: int
    part: Part
    response_id: str
    type: Literal['response.content_part.added']
