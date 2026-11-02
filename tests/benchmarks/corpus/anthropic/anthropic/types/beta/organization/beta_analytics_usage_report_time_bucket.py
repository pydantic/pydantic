
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import List
from datetime import datetime
from ...._models import BaseModel
from .beta_analytics_usage_bucketed_result import BetaAnalyticsUsageBucketedResult

class BetaAnalyticsUsageReportTimeBucket(BaseModel):
    ending_at: datetime
    results: List[BetaAnalyticsUsageBucketedResult]
    starting_at: datetime
