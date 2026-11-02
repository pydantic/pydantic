# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Optional
from ..._models import BaseModel
from .transcription_segment import TranscriptionSegment

class TranslationVerbose(BaseModel):
    duration: float
    language: str
    text: str
    segments: Optional[List[TranscriptionSegment]] = None
