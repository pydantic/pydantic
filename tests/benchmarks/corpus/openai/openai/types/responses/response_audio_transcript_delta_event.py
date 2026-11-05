# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class ResponseAudioTranscriptDeltaEvent(BaseModel):
    """Emitted when there is a partial transcript of audio."""
    delta: str
    sequence_number: int
    type: Literal['response.audio.transcript.delta']
