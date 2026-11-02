# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Optional
from typing_extensions import Literal
from ..._models import BaseModel

class Logprob(BaseModel):
    token: Optional[str] = None
    bytes: Optional[List[int]] = None
    logprob: Optional[float] = None

class TranscriptionTextDeltaEvent(BaseModel):
    """Emitted when there is an additional text delta.

    This is also the first event emitted when the transcription starts. Only emitted when you [create a transcription](https://developers.openai.com/api/reference/resources/audio/subresources/transcriptions/methods/create) with the `Stream` parameter set to `true`.
    """
    delta: str
    type: Literal['transcript.text.delta']
    logprobs: Optional[List[Logprob]] = None
    segment_id: Optional[str] = None
