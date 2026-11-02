
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from datetime import datetime
from typing_extensions import Literal
from ...._models import BaseModel
from .beta_managed_agents_span_model_usage import BetaManagedAgentsSpanModelUsage

class BetaManagedAgentsSpanOutcomeEvaluationEndEvent(BaseModel):
    """Emitted when an outcome evaluation cycle completes.

    Carries the verdict and aggregate token usage. A verdict of `needs_revision` means another evaluation cycle follows; `satisfied`, `max_iterations_reached`, `failed`, or `interrupted` are terminal — no further evaluation cycles follow.
    """
    id: str
    explanation: str
    iteration: int
    outcome_evaluation_start_id: str
    outcome_id: str
    processed_at: datetime
    result: str
    type: Literal['span.outcome_evaluation_end']
    usage: BetaManagedAgentsSpanModelUsage
