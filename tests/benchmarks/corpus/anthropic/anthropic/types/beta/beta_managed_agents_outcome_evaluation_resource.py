
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from datetime import datetime
from typing_extensions import Literal
from ..._models import BaseModel

class BetaManagedAgentsOutcomeEvaluationResource(BaseModel):
    """Evaluation state for a single outcome defined via a `define_outcome` event."""
    completed_at: Optional[datetime] = None
    description: str
    explanation: Optional[str] = None
    iteration: int
    outcome_id: str
    result: str
    type: Literal['outcome_evaluation']
