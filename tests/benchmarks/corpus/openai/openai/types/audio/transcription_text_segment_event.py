# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class TranscriptionTextSegmentEvent(BaseModel):
    """
    Emitted when a diarized transcription returns a completed segment with speaker information. Only emitted when you [create a transcription](https://developers.openai.com/api/reference/resources/audio/subresources/transcriptions/methods/create) with `stream` set to `true` and `response_format` set to `diarized_json`.
    """
    id: str
    end: float
    speaker: str
    start: float
    text: str
    type: Literal['transcript.text.segment']
