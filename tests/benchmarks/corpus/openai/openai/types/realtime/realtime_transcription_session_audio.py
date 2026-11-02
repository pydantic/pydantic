# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from ..._models import BaseModel
from .realtime_transcription_session_audio_input import RealtimeTranscriptionSessionAudioInput

class RealtimeTranscriptionSessionAudio(BaseModel):
    """Configuration for input and output audio."""
    input: Optional[RealtimeTranscriptionSessionAudioInput] = None
