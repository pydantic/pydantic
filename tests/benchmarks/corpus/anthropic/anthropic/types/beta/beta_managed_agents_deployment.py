
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Dict, List, Optional
from datetime import datetime
from typing_extensions import Literal
from ..._models import BaseModel
from .beta_managed_agents_schedule import BetaManagedAgentsSchedule
from .beta_managed_agents_budget_limit import BetaManagedAgentsBudgetLimit
from .beta_managed_agents_agent_reference import BetaManagedAgentsAgentReference
from .beta_managed_agents_deployment_status import BetaManagedAgentsDeploymentStatus
from .beta_managed_agents_session_resource_config import BetaManagedAgentsSessionResourceConfig
from .beta_managed_agents_deployment_initial_event import BetaManagedAgentsDeploymentInitialEvent
from .beta_managed_agents_deployment_paused_reason import BetaManagedAgentsDeploymentPausedReason

class BetaManagedAgentsDeployment(BaseModel):
    """
    A deployment is a configured instance of an agent — it binds the agent to everything needed to run it autonomously: an environment, credentials, initial events, and an optional schedule.
    """
    id: str
    agent: BetaManagedAgentsAgentReference
    archived_at: Optional[datetime] = None
    created_at: datetime
    description: Optional[str] = None
    environment_id: str
    initial_events: List[BetaManagedAgentsDeploymentInitialEvent]
    metadata: Dict[str, str]
    name: str
    paused_reason: Optional[BetaManagedAgentsDeploymentPausedReason] = None
    resources: List[BetaManagedAgentsSessionResourceConfig]
    schedule: Optional[BetaManagedAgentsSchedule] = None
    status: BetaManagedAgentsDeploymentStatus
    type: Literal['deployment']
    updated_at: datetime
    vault_ids: List[str]
    budget: Optional[BetaManagedAgentsBudgetLimit] = None
