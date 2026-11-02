
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from ...._models import BaseModel
from .beta_analytics_skill_office_product_metrics import BetaAnalyticsSkillOfficeProductMetrics

class BetaAnalyticsSkillOfficeMetrics(BaseModel):
    """
    Office Agent activity metrics for a single skill on a given day, broken out by Office product.
    """
    excel: BetaAnalyticsSkillOfficeProductMetrics
    outlook: BetaAnalyticsSkillOfficeProductMetrics
    powerpoint: BetaAnalyticsSkillOfficeProductMetrics
    word: BetaAnalyticsSkillOfficeProductMetrics
