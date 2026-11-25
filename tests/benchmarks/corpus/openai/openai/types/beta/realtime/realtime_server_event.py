
# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...._models import BaseModel
from .conversation_item import ConversationItem

class ConversationItemRetrieved(BaseModel):
    event_id: str
    item: ConversationItem
    type: Literal['conversation.item.retrieved']

class OutputAudioBufferStarted(BaseModel):
    event_id: str
    response_id: str
    type: Literal['output_audio_buffer.started']

class OutputAudioBufferStopped(BaseModel):
    event_id: str
    response_id: str
    type: Literal['output_audio_buffer.stopped']

class OutputAudioBufferCleared(BaseModel):
    event_id: str
    response_id: str
    type: Literal['output_audio_buffer.cleared']
