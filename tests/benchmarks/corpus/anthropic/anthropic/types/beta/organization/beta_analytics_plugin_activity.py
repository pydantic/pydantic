
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from ...._models import BaseModel
from .beta_analytics_plugin_cowork_metrics import BetaAnalyticsPluginCoworkMetrics
from .beta_analytics_plugin_claude_code_metrics import BetaAnalyticsPluginClaudeCodeMetrics

class ChatCoworkUnifiedMetrics(BaseModel):
    """
    Plugin use recorded while members had Chat and Cowork unified (Cowork's features inside claude.ai chat) turned on. A count is null in date-range mode where it cannot be computed. Omitted from the response on deployments that do not offer Chat and Cowork unified.
    """
    distinct_session_plugin_used_count: Optional[int] = None

class BetaAnalyticsPluginActivity(BaseModel):
    """Per-plugin install + invocation activity for a given day.

    With `group_by[]=user_id` / `rbac_group_id` / `product` (`cowork`,
    `claude_code` and `chat_cowork_unified` only on this endpoint) each row is
    one (plugin, user), (plugin, group), or (plugin, product) cut: the flat
    `user_id` / `rbac_group_id` / `product` keys carry the cut and the counts
    are scoped to it.
    """
    claude_code_metrics: BetaAnalyticsPluginClaudeCodeMetrics
    cowork_metrics: BetaAnalyticsPluginCoworkMetrics
    distinct_user_count: int
    install_count: Optional[int] = None
    invocation_count: int
    plugin_name: str
    chat_cowork_unified_metrics: Optional[ChatCoworkUnifiedMetrics] = None
    plugin_id: Optional[str] = None
    product: Optional[str] = None
    rbac_group_id: Optional[str] = None
    rbac_group_name: Optional[str] = None
    user_id: Optional[str] = None
