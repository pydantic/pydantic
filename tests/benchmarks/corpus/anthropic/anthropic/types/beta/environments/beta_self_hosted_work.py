
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Dict, Optional
from typing_extensions import Literal
from ...._models import BaseModel
from .beta_session_work_data import BetaSessionWorkData

class BetaSelfHostedWork(BaseModel):
    """Work resource representing a unit of work in a self-hosted environment.

    Work items are queued when sessions are created or when long-dormant sessions
    receive new messages. The environment worker polls for work to execute in a
    self-hosted sandbox.
    """
    id: str
    acknowledged_at: Optional[str] = None
    created_at: str
    data: BetaSessionWorkData
    environment_id: str
    latest_heartbeat_at: Optional[str] = None
    metadata: Dict[str, str]
    secret: Optional[str] = None
    started_at: Optional[str] = None
    state: Literal['queued', 'starting', 'active', 'stopping', 'stopped']
    stop_requested_at: Optional[str] = None
    stopped_at: Optional[str] = None
    type: Literal['work']
