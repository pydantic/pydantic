
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from datetime import datetime
from typing_extensions import Literal
from ...._models import BaseModel

class BetaManagedAgentsWorkflowRunPhaseEndedEvent(BaseModel):
    """A workflow run's plan left a phase, or the run's end closed it.

    Emitted once for every `workflow_run.phase_started` event, before the run's `workflow_run.status_ended` event. The event does not say whether the plan finished the phase's work, or why it left.
    """
    id: str
    phase_started_id: str
    processed_at: datetime
    type: Literal['workflow_run.phase_ended']
    workflow_run_id: str
    workflow_run_phase_id: str
