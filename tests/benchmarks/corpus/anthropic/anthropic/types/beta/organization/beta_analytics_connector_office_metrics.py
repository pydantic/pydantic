
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from ...._models import BaseModel
from .beta_analytics_connector_office_product_metrics import BetaAnalyticsConnectorOfficeProductMetrics

class BetaAnalyticsConnectorOfficeMetrics(BaseModel):
    """
    Office Agent activity metrics for a single connector on a given day, broken out by Office product.
    """
    excel: BetaAnalyticsConnectorOfficeProductMetrics
    outlook: BetaAnalyticsConnectorOfficeProductMetrics
    powerpoint: BetaAnalyticsConnectorOfficeProductMetrics
    word: BetaAnalyticsConnectorOfficeProductMetrics
