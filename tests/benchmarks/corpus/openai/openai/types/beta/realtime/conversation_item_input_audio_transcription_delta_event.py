
# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Optional
from typing_extensions import Literal
from ...._models import BaseModel

class Logprob(BaseModel):
    token: str
    bytes: List[int]
    logprob: float

class ConversationItemInputAudioTranscriptionDeltaEvent(BaseModel):
    event_id: str
    item_id: str
    type: Literal['conversation.item.input_audio_transcription.delta']
    content_index: Optional[int] = None
    delta: Optional[str] = None
    logprobs: Optional[List[Logprob]] = None
