
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from .._models import BaseModel
from .capability_support import CapabilitySupport

class ContextManagementCapability(BaseModel):
    """Context management capability details."""
    clear_thinking_20251015: Optional[CapabilitySupport] = None
    clear_tool_uses_20250919: Optional[CapabilitySupport] = None
    compact_20260112: Optional[CapabilitySupport] = None
    supported: bool
