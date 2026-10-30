
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from ...._models import BaseModel

class BetaAnalyticsOfficeProductMetrics(BaseModel):
    """
    Office Agent activity metrics for a single user on a given day within one Office product.
    """
    connectors_used_count: int
    distinct_connectors_used_count: Optional[int] = None
    distinct_session_count: Optional[int] = None
    distinct_skills_used_count: Optional[int] = None
    message_count: int
    skills_used_count: int
