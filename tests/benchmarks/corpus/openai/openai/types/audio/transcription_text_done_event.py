# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Optional
from typing_extensions import Literal
from ..._models import BaseModel
from .transcription_language import TranscriptionLanguage

class Logprob(BaseModel):
    token: Optional[str] = None
    bytes: Optional[List[int]] = None
    logprob: Optional[float] = None

class UsageInputTokenDetails(BaseModel):
    """Details about the input tokens billed for this request."""
    audio_tokens: Optional[int] = None
    text_tokens: Optional[int] = None

class Usage(BaseModel):
    """Usage statistics for models billed by token usage."""
    input_tokens: int
    output_tokens: int
    total_tokens: int
    type: Literal['tokens']
    input_token_details: Optional[UsageInputTokenDetails] = None

class TranscriptionTextDoneEvent(BaseModel):
    """Emitted when the transcription is complete.

    Contains the complete transcription text. Only emitted when you [create a transcription](https://developers.openai.com/api/reference/resources/audio/subresources/transcriptions/methods/create) with the `Stream` parameter set to `true`.
    """
    text: str
    type: Literal['transcript.text.done']
    languages: Optional[List[TranscriptionLanguage]] = None
    logprobs: Optional[List[Logprob]] = None
    usage: Optional[Usage] = None
