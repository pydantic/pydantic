# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Optional
from typing_extensions import Literal
from ..._models import BaseModel
from .transcription_word import TranscriptionWord
from .transcription_segment import TranscriptionSegment

class Usage(BaseModel):
    """Usage statistics for models billed by audio input duration."""
    seconds: float
    type: Literal['duration']

class TranscriptionVerbose(BaseModel):
    """
    Represents a verbose json transcription response returned by model, based on the provided input.
    """
    duration: float
    language: str
    text: str
    segments: Optional[List[TranscriptionSegment]] = None
    usage: Optional[Usage] = None
    words: Optional[List[TranscriptionWord]] = None
