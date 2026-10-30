# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from ..._models import BaseModel

class InputTokensDetails(BaseModel):
    """A detailed breakdown of the input tokens."""
    cache_write_tokens: int
    cached_tokens: int

class OutputTokensDetails(BaseModel):
    """A detailed breakdown of the output tokens."""
    reasoning_tokens: int

class BetaResponseUsage(BaseModel):
    """
    Represents token usage details including input tokens, output tokens,
    a breakdown of output tokens, and the total tokens used.
    """
    input_tokens: int
    input_tokens_details: InputTokensDetails
    output_tokens: int
    output_tokens_details: OutputTokensDetails
    total_tokens: int
