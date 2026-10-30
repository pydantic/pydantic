
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from datetime import datetime
from ....._models import BaseModel
from .beta_analytics_usage_group import BetaAnalyticsUsageGroup
from .beta_analytics_usage_metrics import BetaAnalyticsUsageMetrics

class BetaAnalyticsUsageItem(BaseModel):
    ending_at: datetime
    group: BetaAnalyticsUsageGroup
    starting_at: datetime
    usage: BetaAnalyticsUsageMetrics
