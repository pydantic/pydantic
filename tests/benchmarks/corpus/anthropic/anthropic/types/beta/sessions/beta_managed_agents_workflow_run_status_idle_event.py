
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from datetime import datetime
from typing_extensions import Literal
from ...._models import BaseModel

class BetaManagedAgentsWorkflowRunStatusIdleEvent(BaseModel):
    """A workflow run is idle.

    Emitted each time the run goes idle, whatever the cause. If the run ends while idle, no `workflow_run.status_running` comes between this event and its `workflow_run.status_ended`.
    """
    id: str
    processed_at: datetime
    type: Literal['workflow_run.status_idle']
    workflow_run_id: str
