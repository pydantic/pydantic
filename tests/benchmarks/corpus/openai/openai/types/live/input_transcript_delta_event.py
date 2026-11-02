# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class InputTranscriptDeltaEvent(BaseModel):
    """A transcript fragment for user input audio in the Live session.

    Accumulate fragments in delivery order; these events do not define complete turns or include a transcript-done event.
    """
    delta: str
    end_ms: int
    event_id: str
    start_ms: int
    type: Literal['session.input_transcript.delta']
    client_event_id: Optional[str] = None
