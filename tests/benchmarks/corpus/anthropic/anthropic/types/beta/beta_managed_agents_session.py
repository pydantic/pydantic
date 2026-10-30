
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Dict, List, Optional
from datetime import datetime
from typing_extensions import Literal
from ..._models import BaseModel
from .beta_managed_agents_budget_limit import BetaManagedAgentsBudgetLimit
from .beta_managed_agents_session_agent import BetaManagedAgentsSessionAgent
from .beta_managed_agents_session_stats import BetaManagedAgentsSessionStats
from .beta_managed_agents_session_usage import BetaManagedAgentsSessionUsage
from .sessions.beta_managed_agents_session_resource import BetaManagedAgentsSessionResource
from .beta_managed_agents_outcome_evaluation_resource import BetaManagedAgentsOutcomeEvaluationResource

class BetaManagedAgentsSession(BaseModel):
    """A Managed Agents `session`."""
    id: str
    agent: BetaManagedAgentsSessionAgent
    archived_at: Optional[datetime] = None
    budget: Optional[BetaManagedAgentsBudgetLimit] = None
    created_at: datetime
    environment_id: str
    metadata: Dict[str, str]
    outcome_evaluations: List[BetaManagedAgentsOutcomeEvaluationResource]
    resources: List[BetaManagedAgentsSessionResource]
    stats: BetaManagedAgentsSessionStats
    status: Literal['rescheduling', 'running', 'idle', 'terminated']
    title: Optional[str] = None
    type: Literal['session']
    updated_at: datetime
    usage: BetaManagedAgentsSessionUsage
    vault_ids: List[str]
    deployment_id: Optional[str] = None
