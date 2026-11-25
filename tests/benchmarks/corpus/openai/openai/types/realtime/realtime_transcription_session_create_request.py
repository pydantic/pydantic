# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Optional
from typing_extensions import Literal
from ..._models import BaseModel
from .realtime_transcription_session_audio import RealtimeTranscriptionSessionAudio

class RealtimeTranscriptionSessionCreateRequest(BaseModel):
    """Realtime transcription session object configuration."""
    type: Literal['transcription']
    audio: Optional[RealtimeTranscriptionSessionAudio] = None
    include: Optional[List[Literal['item.input_audio_transcription.logprobs']]] = None
