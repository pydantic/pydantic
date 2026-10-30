
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from ...._models import BaseModel

class BetaAnalyticsDesignMetrics(BaseModel):
    """Claude Design activity metrics for a single user on a given day."""
    distinct_projects_created_count: int
    distinct_projects_used_count: Optional[int] = None
    distinct_session_count: Optional[int] = None
    message_count: int
