
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from ...._models import BaseModel

class BetaAnalyticsConnectorOfficeProductMetrics(BaseModel):
    """
    Office Agent activity metrics for a single connector on a given day within one Office product.
    """
    distinct_session_connector_used_count: Optional[int] = None
