
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from datetime import datetime
from typing_extensions import Literal
from ...._models import BaseModel

class BetaManagedAgentsWorkflowRunPhaseStartedEvent(BaseModel):
    """A workflow run's plan entered a phase."""
    id: str
    processed_at: datetime
    type: Literal['workflow_run.phase_started']
    workflow_run_id: str
    workflow_run_phase_id: str
