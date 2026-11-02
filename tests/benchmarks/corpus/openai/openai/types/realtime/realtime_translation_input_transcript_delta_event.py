# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class RealtimeTranslationInputTranscriptDeltaEvent(BaseModel):
    """Returned when optional source-language transcript text is available.

    This event
    is emitted only when `audio.input.transcription` is configured.

    Transcript deltas are append-only text fragments. Clients should not insert
    unconditional spaces between deltas.
    """
    delta: str
    event_id: str
    type: Literal['session.input_transcript.delta']
    elapsed_ms: Optional[int] = None
