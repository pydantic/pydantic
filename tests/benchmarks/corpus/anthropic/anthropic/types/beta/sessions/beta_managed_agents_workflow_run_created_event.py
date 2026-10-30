
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import List, Optional
from datetime import datetime
from typing_extensions import Literal
from ...._models import BaseModel
from .beta_managed_agents_workflow_run_phase import BetaManagedAgentsWorkflowRunPhase

class BetaManagedAgentsWorkflowRunCreatedEvent(BaseModel):
    """A workflow run was created.

    A workflow run is background work that the session's agent starts. Emitted once per run, before the run's other `workflow_run.*` events.
    """
    id: str
    description: Optional[str] = None
    name: str
    phases: List[BetaManagedAgentsWorkflowRunPhase]
    processed_at: datetime
    type: Literal['workflow_run.created']
    workflow_run_id: str
