
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Union, Optional
from datetime import datetime
from typing_extensions import Literal, Annotated, TypeAlias
from ...._models import BaseModel, UnionDiscriminator
from ..beta_managed_agents_advisor import BetaManagedAgentsAdvisor
from .beta_managed_agents_inline_agent import BetaManagedAgentsInlineAgent
from .beta_managed_agents_session_thread_stats import BetaManagedAgentsSessionThreadStats
from .beta_managed_agents_session_thread_usage import BetaManagedAgentsSessionThreadUsage
from ..beta_managed_agents_session_thread_agent import BetaManagedAgentsSessionThreadAgent
from .beta_managed_agents_session_thread_status import BetaManagedAgentsSessionThreadStatus
Agent: TypeAlias = Annotated[Union[BetaManagedAgentsSessionThreadAgent, BetaManagedAgentsAdvisor, BetaManagedAgentsInlineAgent], UnionDiscriminator('type')]

class BetaManagedAgentsSessionThread(BaseModel):
    """An execution thread within a `session`.

    Each session has one primary thread plus zero or more child threads.
    """
    id: str
    agent: Agent
    archived_at: Optional[datetime] = None
    created_at: datetime
    parent_thread_id: Optional[str] = None
    session_id: str
    stats: Optional[BetaManagedAgentsSessionThreadStats] = None
    status: BetaManagedAgentsSessionThreadStatus
    type: Literal['session_thread']
    updated_at: datetime
    usage: Optional[BetaManagedAgentsSessionThreadUsage] = None
    workflow_run_id: Optional[str] = None
