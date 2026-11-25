
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from ...._models import BaseModel

class BetaAnalyticsScienceMetrics(BaseModel):
    """Claude Science activity metrics for a single user on a given day."""
    delegation_count: int
    distinct_session_count: Optional[int] = None
    message_count: int
    remote_compute_job_count: int
    skills_used_count: int
