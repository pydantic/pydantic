
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from ..._models import BaseModel
from .beta_count_tokens_context_management_response import BetaCountTokensContextManagementResponse

class BetaMessageTokensCount(BaseModel):
    context_management: Optional[BetaCountTokensContextManagementResponse] = None
    input_tokens: int
