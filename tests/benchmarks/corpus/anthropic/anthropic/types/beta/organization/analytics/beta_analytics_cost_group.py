
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from ....._models import BaseModel
from ..beta_analytics_actor import BetaAnalyticsActor
from ..beta_analytics_speed import BetaAnalyticsSpeed
from ..beta_analytics_actor_type import BetaAnalyticsActorType
from ..beta_analytics_token_type import BetaAnalyticsTokenType
from ..beta_analytics_service_tier import BetaAnalyticsServiceTier
from ..beta_analytics_context_window import BetaAnalyticsContextWindow
from ..beta_analytics_grouped_cost_type import BetaAnalyticsGroupedCostType
from ..beta_analytics_claude_tag_category import BetaAnalyticsClaudeTagCategory
from ..beta_analytics_usage_cost_inference_geo import BetaAnalyticsUsageCostInferenceGeo

class BetaAnalyticsCostGroup(BaseModel):
    """
    The dimension values one cost row is broken out by, including
    `cost_type` and `token_type`.
    """
    actor: Optional[BetaAnalyticsActor] = None
    actor_type: Optional[BetaAnalyticsActorType] = None
    agent_id: Optional[str] = None
    api_key_id: Optional[str] = None
    claude_tag_category: Optional[BetaAnalyticsClaudeTagCategory] = None
    claude_tag_user_id: Optional[str] = None
    context_window: Optional[BetaAnalyticsContextWindow] = None
    cost_type: Optional[BetaAnalyticsGroupedCostType] = None
    deployment_id: Optional[str] = None
    environment_id: Optional[str] = None
    inference_geo: Optional[BetaAnalyticsUsageCostInferenceGeo] = None
    model: Optional[str] = None
    product: Optional[str] = None
    rbac_group_id: Optional[str] = None
    service_tier: Optional[BetaAnalyticsServiceTier] = None
    session_id: Optional[str] = None
    slack_channel_id: Optional[str] = None
    speed: Optional[BetaAnalyticsSpeed] = None
    token_type: Optional[BetaAnalyticsTokenType] = None
    user_profile_id: Optional[str] = None
    workspace_id: Optional[str] = None
