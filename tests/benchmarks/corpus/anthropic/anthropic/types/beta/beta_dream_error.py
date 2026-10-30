
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from ..._models import BaseModel

class BetaDreamError(BaseModel):
    """Failure detail for a Dream whose `status` is `failed`."""
    message: str
    type: str
