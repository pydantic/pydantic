
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from datetime import datetime
from typing_extensions import Literal
from ...._models import BaseModel

class BetaManagedAgentsWorkflowRunStatusRunningEvent(BaseModel):
    """A workflow run is running.

    Emitted when the run starts to execute, and each time it resumes after being idle. A run that starts idle emits `workflow_run.status_idle` first.
    """
    id: str
    processed_at: datetime
    type: Literal['workflow_run.status_running']
    workflow_run_id: str
