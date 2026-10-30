
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...._models import BaseModel

class BetaSelfHostedWorkHeartbeatResponse(BaseModel):
    """Response after recording a heartbeat for a work item."""
    last_heartbeat: str
    lease_extended: bool
    state: Literal['queued', 'starting', 'active', 'stopping', 'stopped']
    ttl_seconds: int
    type: Literal['work_heartbeat']
