
# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ...._models import BaseModel

class ConversationItemContent(BaseModel):
    id: Optional[str] = None
    audio: Optional[str] = None
    text: Optional[str] = None
    transcript: Optional[str] = None
    type: Optional[Literal['input_text', 'input_audio', 'item_reference', 'text', 'audio']] = None
