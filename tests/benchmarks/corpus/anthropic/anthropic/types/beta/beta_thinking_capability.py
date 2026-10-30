
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from ..._models import BaseModel
from .beta_thinking_types import BetaThinkingTypes

class BetaThinkingCapability(BaseModel):
    """Thinking capability details."""
    supported: bool
    types: BetaThinkingTypes
