
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from ..._models import BaseModel
from .beta_capability_support import BetaCapabilitySupport

class BetaContextManagementCapability(BaseModel):
    """Context management capability details."""
    clear_thinking_20251015: Optional[BetaCapabilitySupport] = None
    clear_tool_uses_20250919: Optional[BetaCapabilitySupport] = None
    compact_20260112: Optional[BetaCapabilitySupport] = None
    supported: bool
