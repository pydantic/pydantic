
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel
from .beta_cache_creation import BetaCacheCreation

class BetaCompactionIterationUsage(BaseModel):
    """Token usage for a compaction iteration."""
    cache_creation: Optional[BetaCacheCreation] = None
    cache_creation_input_tokens: int
    cache_read_input_tokens: int
    input_tokens: int
    output_tokens: int
    type: Literal['compaction']
