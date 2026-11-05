
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from ..._models import BaseModel
from .beta_iterations_usage import BetaIterationsUsage
from .beta_server_tool_usage import BetaServerToolUsage
from .beta_fallback_credit_usage import BetaFallbackCreditUsage
from .beta_output_tokens_details import BetaOutputTokensDetails

class BetaMessageDeltaUsage(BaseModel):
    cache_creation_input_tokens: Optional[int] = None
    cache_read_input_tokens: Optional[int] = None
    fallback_credit: Optional[BetaFallbackCreditUsage] = None
    input_tokens: Optional[int] = None
    iterations: Optional[BetaIterationsUsage] = None
    output_tokens: int
    output_tokens_details: Optional[BetaOutputTokensDetails] = None
    server_tool_use: Optional[BetaServerToolUsage] = None
