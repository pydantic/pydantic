
# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ...._models import BaseModel

class Error(BaseModel):
    code: Optional[str] = None
    message: Optional[str] = None
    param: Optional[str] = None
    type: Optional[str] = None

class ConversationItemInputAudioTranscriptionFailedEvent(BaseModel):
    content_index: int
    error: Error
    event_id: str
    item_id: str
    type: Literal['conversation.item.input_audio_transcription.failed']
