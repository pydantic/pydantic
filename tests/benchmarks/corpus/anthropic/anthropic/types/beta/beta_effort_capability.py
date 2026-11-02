
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from ..._models import BaseModel
from .beta_capability_support import BetaCapabilitySupport

class BetaEffortCapability(BaseModel):
    """Effort (reasoning_effort) capability details."""
    high: BetaCapabilitySupport
    low: BetaCapabilitySupport
    max: BetaCapabilitySupport
    medium: BetaCapabilitySupport
    supported: bool
    xhigh: Optional[BetaCapabilitySupport] = None
