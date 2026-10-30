
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from datetime import datetime
from ....._models import BaseModel
from .beta_analytics_cost_group import BetaAnalyticsCostGroup
from .beta_analytics_cost_metrics import BetaAnalyticsCostMetrics

class BetaAnalyticsCostItem(BaseModel):
    cost: BetaAnalyticsCostMetrics
    ending_at: datetime
    group: BetaAnalyticsCostGroup
    starting_at: datetime
