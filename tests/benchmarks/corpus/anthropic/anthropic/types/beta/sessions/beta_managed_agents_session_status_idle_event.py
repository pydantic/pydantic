
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Union, Optional
from datetime import datetime
from typing_extensions import Literal, Annotated, TypeAlias
from ...._models import BaseModel, UnionDiscriminator
from .beta_managed_agents_session_refusal import BetaManagedAgentsSessionRefusal
from .beta_managed_agents_session_end_turn import BetaManagedAgentsSessionEndTurn
from .beta_managed_agents_session_budget_reached import BetaManagedAgentsSessionBudgetReached
from .beta_managed_agents_session_requires_action import BetaManagedAgentsSessionRequiresAction
from .beta_managed_agents_session_retries_exhausted import BetaManagedAgentsSessionRetriesExhausted
from .beta_managed_agents_session_refusal_stop_details import BetaManagedAgentsSessionRefusalStopDetails
StopReason: TypeAlias = Annotated[Union[BetaManagedAgentsSessionEndTurn, BetaManagedAgentsSessionRequiresAction, BetaManagedAgentsSessionRetriesExhausted, BetaManagedAgentsSessionBudgetReached, BetaManagedAgentsSessionRefusal], UnionDiscriminator('type')]

class BetaManagedAgentsSessionStatusIdleEvent(BaseModel):
    """Indicates the agent has paused and is awaiting user input."""
    id: str
    processed_at: datetime
    stop_details: Optional[BetaManagedAgentsSessionRefusalStopDetails] = None
    stop_reason: StopReason
    type: Literal['session.status_idle']
