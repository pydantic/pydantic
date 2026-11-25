# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from .._models import BaseModel

class CompletionTokensDetails(BaseModel):
    """Breakdown of tokens used in a completion."""
    accepted_prediction_tokens: Optional[int] = None
    audio_tokens: Optional[int] = None
    reasoning_tokens: Optional[int] = None
    rejected_prediction_tokens: Optional[int] = None
    text_tokens: Optional[int] = None

class PromptTokensDetails(BaseModel):
    """Breakdown of tokens used in the prompt."""
    audio_tokens: Optional[int] = None
    cache_write_tokens: Optional[int] = None
    cached_tokens: Optional[int] = None
    image_tokens: Optional[int] = None
    text_tokens: Optional[int] = None

class CompletionUsage(BaseModel):
    """Usage statistics for the completion request."""
    completion_tokens: int
    prompt_tokens: int
    total_tokens: int
    completion_tokens_details: Optional[CompletionTokensDetails] = None
    prompt_tokens_details: Optional[PromptTokensDetails] = None
