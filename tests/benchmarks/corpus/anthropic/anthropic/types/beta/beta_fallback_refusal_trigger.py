
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class BetaFallbackRefusalTrigger(BaseModel):
    """The `from` model declined for policy reasons."""
    category: Optional[Literal['cyber', 'bio', 'frontier_llm', 'reasoning_extraction', 'general_harms']] = None
    type: Literal['refusal']
