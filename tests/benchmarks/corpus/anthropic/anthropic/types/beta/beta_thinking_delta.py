
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class BetaThinkingDelta(BaseModel):
    estimated_tokens: Optional[int] = None
    thinking: str
    type: Literal['thinking_delta']
