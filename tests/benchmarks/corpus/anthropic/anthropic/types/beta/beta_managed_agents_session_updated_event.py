
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Dict, Optional
from datetime import datetime
from typing_extensions import Literal
from ..._models import BaseModel
from .beta_managed_agents_budget_limit import BetaManagedAgentsBudgetLimit
from .beta_managed_agents_session_agent import BetaManagedAgentsSessionAgent

class BetaManagedAgentsSessionUpdatedEvent(BaseModel):
    """Emitted when an UpdateSession request changed at least one field.

    Carries only the fields that changed; absent fields were not part of the update. The new configuration applies from the next turn.
    """
    id: str
    processed_at: datetime
    type: Literal['session.updated']
    agent: Optional[BetaManagedAgentsSessionAgent] = None
    budget: Optional[BetaManagedAgentsBudgetLimit] = None
    metadata: Optional[Dict[str, str]] = None
    title: Optional[str] = None
