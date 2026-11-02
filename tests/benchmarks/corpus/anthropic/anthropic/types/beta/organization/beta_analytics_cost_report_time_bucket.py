
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import List
from datetime import datetime
from ...._models import BaseModel
from .beta_analytics_cost_bucketed_result import BetaAnalyticsCostBucketedResult

class BetaAnalyticsCostReportTimeBucket(BaseModel):
    ending_at: datetime
    results: List[BetaAnalyticsCostBucketedResult]
    starting_at: datetime
