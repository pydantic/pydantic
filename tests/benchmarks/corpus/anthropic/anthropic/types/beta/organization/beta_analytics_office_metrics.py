
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from ...._models import BaseModel
from .beta_analytics_office_product_metrics import BetaAnalyticsOfficeProductMetrics

class BetaAnalyticsOfficeMetrics(BaseModel):
    """
    Office Agent activity metrics for a single user on a given day, broken out by Office product.
    """
    excel: BetaAnalyticsOfficeProductMetrics
    outlook: BetaAnalyticsOfficeProductMetrics
    powerpoint: BetaAnalyticsOfficeProductMetrics
    word: BetaAnalyticsOfficeProductMetrics
