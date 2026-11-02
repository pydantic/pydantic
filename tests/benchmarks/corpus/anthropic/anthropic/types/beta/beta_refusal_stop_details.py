
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class BetaRefusalStopDetails(BaseModel):
    """Structured information about a refusal."""
    category: Optional[Literal['cyber', 'bio', 'frontier_llm', 'reasoning_extraction', 'general_harms']] = None
    explanation: Optional[str] = None
    fallback_credit_token: Optional[str] = None
    fallback_has_prefill_claim: Optional[bool] = None
    recommended_model: Optional[str] = None
    type: Literal['refusal']
