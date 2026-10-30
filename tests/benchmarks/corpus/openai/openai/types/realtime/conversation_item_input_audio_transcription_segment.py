# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class ConversationItemInputAudioTranscriptionSegment(BaseModel):
    """Returned when an input audio transcription segment is identified for an item."""
    id: str
    content_index: int
    end: float
    event_id: str
    item_id: str
    speaker: str
    start: float
    text: str
    type: Literal['conversation.item.input_audio_transcription.segment']
