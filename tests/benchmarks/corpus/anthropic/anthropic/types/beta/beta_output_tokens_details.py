
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from ..._models import BaseModel

class BetaOutputTokensDetails(BaseModel):
    thinking_tokens: int
