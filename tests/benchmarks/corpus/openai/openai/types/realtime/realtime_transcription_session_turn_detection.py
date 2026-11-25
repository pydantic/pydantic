# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from ..._models import BaseModel

class RealtimeTranscriptionSessionTurnDetection(BaseModel):
    """Configuration for turn detection.

    Can be set to `null` to turn off. Server
    VAD means that the model will detect the start and end of speech based on
    audio volume and respond at the end of user speech. For `gpt-realtime-whisper`, this must be `null`; VAD is not supported.
    """
    prefix_padding_ms: Optional[int] = None
    silence_duration_ms: Optional[int] = None
    threshold: Optional[float] = None
    type: Optional[str] = None
