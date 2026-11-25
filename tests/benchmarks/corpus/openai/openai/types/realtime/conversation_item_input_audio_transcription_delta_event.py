# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Optional
from typing_extensions import Literal
from ..._models import BaseModel
from .log_prob_properties import LogProbProperties

class ConversationItemInputAudioTranscriptionDeltaEvent(BaseModel):
    """
    Returned when the text value of an input audio transcription content part is updated with incremental transcription results.
    """
    event_id: str
    item_id: str
    type: Literal['conversation.item.input_audio_transcription.delta']
    content_index: Optional[int] = None
    delta: Optional[str] = None
    logprobs: Optional[List[LogProbProperties]] = None
