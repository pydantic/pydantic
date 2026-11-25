
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from datetime import datetime
from typing_extensions import Literal
from ...._models import BaseModel
from .beta_managed_agents_workflow_run_result import BetaManagedAgentsWorkflowRunResult

class BetaManagedAgentsWorkflowRunStatusEndedEvent(BaseModel):
    """A workflow run ended.

    Emitted once per run, as the last of the run's `workflow_run.*` events.
    """
    id: str
    processed_at: datetime
    result: BetaManagedAgentsWorkflowRunResult
    type: Literal['workflow_run.status_ended']
    workflow_run_id: str
