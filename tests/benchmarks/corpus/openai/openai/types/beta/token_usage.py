# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from ..._models import BaseModel

class InputTokensDetails(BaseModel):
    """A breakdown of the agent's input token usage."""
    cached_tokens: int

class OutputTokensDetails(BaseModel):
    """A breakdown of the agent's output token usage."""
    reasoning_tokens: int

class TokenUsage(BaseModel):
    """Recorded token usage for a session or turn.

    Usage is best effort and may change.
    """
    input_tokens: int
    input_tokens_details: InputTokensDetails
    output_tokens: int
    output_tokens_details: OutputTokensDetails
    total_tokens: int
