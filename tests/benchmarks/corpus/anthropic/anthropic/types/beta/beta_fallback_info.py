
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from ..model import Model
from ..._models import BaseModel

class BetaFallbackInfo(BaseModel):
    """Identifies one hop of a fallback transition."""
    model: Model
