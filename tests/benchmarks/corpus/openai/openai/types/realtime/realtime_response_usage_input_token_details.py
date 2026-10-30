# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from ..._models import BaseModel

class CachedTokensDetails(BaseModel):
    """Details about the cached tokens used as input for the Response."""
    audio_tokens: Optional[int] = None
    image_tokens: Optional[int] = None
    text_tokens: Optional[int] = None

class RealtimeResponseUsageInputTokenDetails(BaseModel):
    """Details about the input tokens used in the Response.

    Cached tokens are tokens from previous turns in the conversation that are included as context for the current response. Cached tokens here are counted as a subset of input tokens, meaning input tokens will include cached and uncached tokens.
    """
    audio_tokens: Optional[int] = None
    cached_tokens: Optional[int] = None
    cached_tokens_details: Optional[CachedTokensDetails] = None
    image_tokens: Optional[int] = None
    text_tokens: Optional[int] = None
