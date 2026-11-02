
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from datetime import datetime
from typing_extensions import Literal
from ...._models import BaseModel

class BetaManagedAgentsSpanOutcomeEvaluationOngoingEvent(BaseModel):
    """Periodic heartbeat emitted while an outcome evaluation cycle is in progress.

    Distinguishes 'evaluation is actively running' from 'evaluation is stuck' between the corresponding `span.outcome_evaluation_start` and `span.outcome_evaluation_end` events.
    """
    id: str
    iteration: int
    outcome_id: str
    processed_at: datetime
    type: Literal['span.outcome_evaluation_ongoing']
