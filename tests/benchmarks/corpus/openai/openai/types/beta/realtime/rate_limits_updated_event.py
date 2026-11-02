
# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Optional
from typing_extensions import Literal
from ...._models import BaseModel

class RateLimit(BaseModel):
    limit: Optional[int] = None
    name: Optional[Literal['requests', 'tokens']] = None
    remaining: Optional[int] = None
    reset_seconds: Optional[float] = None

class RateLimitsUpdatedEvent(BaseModel):
    event_id: str
    rate_limits: List[RateLimit]
    type: Literal['rate_limits.updated']
