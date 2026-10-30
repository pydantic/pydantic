
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from ....._models import BaseModel
from ..beta_analytics_actor import BetaAnalyticsActor
from ..beta_analytics_speed import BetaAnalyticsSpeed
from ..beta_analytics_actor_type import BetaAnalyticsActorType
from ..beta_analytics_service_tier import BetaAnalyticsServiceTier
from ..beta_analytics_context_window import BetaAnalyticsContextWindow
from ..beta_analytics_claude_tag_category import BetaAnalyticsClaudeTagCategory
from ..beta_analytics_usage_cost_inference_geo import BetaAnalyticsUsageCostInferenceGeo

class BetaAnalyticsUsageGroup(BaseModel):
    """
    The dimension values one usage row is broken out by; each is null
    unless its dimension is in `group_by[]`.
    """
    actor: Optional[BetaAnalyticsActor] = None
    actor_type: Optional[BetaAnalyticsActorType] = None
    agent_id: Optional[str] = None
    api_key_id: Optional[str] = None
    claude_tag_category: Optional[BetaAnalyticsClaudeTagCategory] = None
    claude_tag_user_id: Optional[str] = None
    context_window: Optional[BetaAnalyticsContextWindow] = None
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
    user_profile_id: Optional[str] = None
    workspace_id: Optional[str] = None
