
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ...._models import BaseModel

class BetaManagedAgentsSpanModelUsage(BaseModel):
    """Token usage for a single model request."""
    cache_creation_input_tokens: int
    cache_read_input_tokens: int
    input_tokens: int
    output_tokens: int
    speed: Optional[Literal['standard', 'fast']] = None
