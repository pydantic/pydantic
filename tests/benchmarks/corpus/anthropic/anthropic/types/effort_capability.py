
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from .._models import BaseModel
from .capability_support import CapabilitySupport

class EffortCapability(BaseModel):
    """Effort (reasoning_effort) capability details."""
    high: CapabilitySupport
    low: CapabilitySupport
    max: CapabilitySupport
    medium: CapabilitySupport
    supported: bool
    xhigh: Optional[CapabilitySupport] = None
