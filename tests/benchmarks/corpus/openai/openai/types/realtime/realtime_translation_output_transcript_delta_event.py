# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class RealtimeTranslationOutputTranscriptDeltaEvent(BaseModel):
    """Returned when translated transcript text is available.

    Transcript deltas are append-only text fragments. Clients should not insert
    unconditional spaces between deltas.
    """
    delta: str
    event_id: str
    type: Literal['session.output_transcript.delta']
    elapsed_ms: Optional[int] = None
