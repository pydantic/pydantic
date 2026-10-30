
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from ...._models import BaseModel
from .beta_analytics_lines_of_code import BetaAnalyticsLinesOfCode

class BetaAnalyticsCoreCodeMetrics(BaseModel):
    """Core Claude Code activity metrics for a single user on a given day."""
    artifacts_created_count: int
    commit_count: int
    distinct_session_count: Optional[int] = None
    lines_of_code: BetaAnalyticsLinesOfCode
    pull_request_count: int
