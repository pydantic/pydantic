
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class BetaManagedAgentsSessionRateLimitedRunError(BaseModel):
    """Session creation was rejected due to rate limiting.

    The schedule keeps firing; subsequent runs may succeed.
    """
    message: str
    type: Literal['session_rate_limited_error']
