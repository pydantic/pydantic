
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from .._models import BaseModel
from .thinking_types import ThinkingTypes

class ThinkingCapability(BaseModel):
    """Thinking capability details."""
    supported: bool
    types: ThinkingTypes
