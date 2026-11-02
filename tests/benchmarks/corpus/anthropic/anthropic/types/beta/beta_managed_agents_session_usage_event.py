
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from datetime import datetime
from typing_extensions import Literal
from ..._models import BaseModel
from .beta_managed_agents_budget_limit import BetaManagedAgentsBudgetLimit
from .sessions.beta_managed_agents_session_usage_snapshot import BetaManagedAgentsSessionUsageSnapshot

class BetaManagedAgentsSessionUsageEvent(BaseModel):
    """Periodic snapshot of the session's cumulative usage and tracked list cost."""
    id: str
    processed_at: datetime
    type: Literal['session.usage']
    usage: BetaManagedAgentsSessionUsageSnapshot
    budget: Optional[BetaManagedAgentsBudgetLimit] = None
