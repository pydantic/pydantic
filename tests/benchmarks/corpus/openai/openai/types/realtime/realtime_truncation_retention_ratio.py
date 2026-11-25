# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class TokenLimits(BaseModel):
    """Optional custom token limits for this truncation strategy.

    If not provided, the model's default token limits will be used.
    """
    post_instructions: Optional[int] = None

class RealtimeTruncationRetentionRatio(BaseModel):
    """
    Retain a fraction of the conversation tokens when the conversation exceeds the input token limit. This allows you to amortize truncations across multiple turns, which can help improve cached token usage.
    """
    retention_ratio: float
    type: Literal['retention_ratio']
    token_limits: Optional[TokenLimits] = None
