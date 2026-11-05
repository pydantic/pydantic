# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias
from ..._utils import PropertyInfo
from ..._models import BaseModel
from .transcription_language import TranscriptionLanguage

class Logprob(BaseModel):
    token: Optional[str] = None
    bytes: Optional[List[float]] = None
    logprob: Optional[float] = None

class UsageTokensInputTokenDetails(BaseModel):
    """Details about the input tokens billed for this request."""
    audio_tokens: Optional[int] = None
    text_tokens: Optional[int] = None

class UsageTokens(BaseModel):
    """Usage statistics for models billed by token usage."""
    input_tokens: int
    output_tokens: int
    total_tokens: int
    type: Literal['tokens']
    input_token_details: Optional[UsageTokensInputTokenDetails] = None

class UsageDuration(BaseModel):
    """Usage statistics for models billed by audio input duration."""
    seconds: float
    type: Literal['duration']
Usage: TypeAlias = Annotated[Union[UsageTokens, UsageDuration], PropertyInfo(discriminator='type')]

class Transcription(BaseModel):
    """
    Represents a transcription response returned by model, based on the provided input.
    """
    text: str
    languages: Optional[List[TranscriptionLanguage]] = None
    logprobs: Optional[List[Logprob]] = None
    usage: Optional[Usage] = None
