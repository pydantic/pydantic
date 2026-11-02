
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from ..._models import BaseModel
from .beta_capability_support import BetaCapabilitySupport

class BetaThinkingTypes(BaseModel):
    """Which `thinking.type` values the model accepts on requests.

    Read each key on its own: for example, `enabled` can be false while `disabled` is true.
    """
    adaptive: BetaCapabilitySupport
    between_tools: BetaCapabilitySupport
    disabled: BetaCapabilitySupport
    enabled: BetaCapabilitySupport
