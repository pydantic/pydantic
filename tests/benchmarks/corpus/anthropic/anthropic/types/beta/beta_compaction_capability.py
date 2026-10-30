
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from ..._models import BaseModel
from .beta_capability_support import BetaCapabilitySupport

class BetaCompactionCapability(BaseModel):
    """
    Compaction capability details: whether the model accepts the top-level
    `compaction` request parameter, with one entry per supported
    `compaction.type` value.
    """
    summarize: BetaCapabilitySupport
    supported: bool
