# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class Error(BaseModel):
    """Details of the transcription error."""
    code: Optional[str] = None
    message: Optional[str] = None
    param: Optional[str] = None
    type: Optional[str] = None

class ConversationItemInputAudioTranscriptionFailedEvent(BaseModel):
    """
    Returned when input audio transcription is configured, and a transcription
    request for a user message failed. These events are separate from other
    `error` events so that the client can identify the related Item.
    """
    content_index: int
    error: Error
    event_id: str
    item_id: str
    type: Literal['conversation.item.input_audio_transcription.failed']
