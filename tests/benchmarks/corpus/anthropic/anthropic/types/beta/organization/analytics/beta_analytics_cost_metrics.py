
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from ....._models import BaseModel

class BetaAnalyticsCostMetrics(BaseModel):
    """The cost of one row."""
    amount: str
    currency: str
    list_amount: str
    requests: Optional[int] = None
