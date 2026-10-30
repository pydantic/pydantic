
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from datetime import datetime
from typing_extensions import Literal
from ...._models import BaseModel

class BetaManagedAgentsSpanOutcomeEvaluationStartEvent(BaseModel):
    """Emitted when an outcome evaluation cycle begins."""
    id: str
    iteration: int
    outcome_id: str
    processed_at: datetime
    type: Literal['span.outcome_evaluation_start']
