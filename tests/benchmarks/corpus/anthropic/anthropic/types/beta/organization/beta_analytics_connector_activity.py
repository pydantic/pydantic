
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from ...._models import BaseModel
from .beta_analytics_connector_chat_metrics import BetaAnalyticsConnectorChatMetrics
from .beta_analytics_connector_cowork_metrics import BetaAnalyticsConnectorCoworkMetrics
from .beta_analytics_connector_office_metrics import BetaAnalyticsConnectorOfficeMetrics
from .beta_analytics_connector_claude_code_metrics import BetaAnalyticsConnectorClaudeCodeMetrics
from .beta_analytics_connector_chat_cowork_unified_chat_metrics import BetaAnalyticsConnectorChatCoworkUnifiedChatMetrics
from .beta_analytics_connector_chat_cowork_unified_sessions_metrics import BetaAnalyticsConnectorChatCoworkUnifiedSessionsMetrics

class ChatCoworkUnifiedMetrics(BaseModel):
    """
    Connector use recorded while members had Chat and Cowork unified (Cowork's features inside claude.ai chat) turned on, split into chat conversations and Cowork sessions. A count is null in date-range mode where it cannot be computed. Omitted from the response on deployments that do not offer Chat and Cowork unified.
    """
    chat: BetaAnalyticsConnectorChatCoworkUnifiedChatMetrics
    sessions: BetaAnalyticsConnectorChatCoworkUnifiedSessionsMetrics

class BetaAnalyticsConnectorActivity(BaseModel):
    """Per-connector activity data for a given day."""
    chat_metrics: BetaAnalyticsConnectorChatMetrics
    claude_code_metrics: BetaAnalyticsConnectorClaudeCodeMetrics
    connector_name: str
    cowork_metrics: BetaAnalyticsConnectorCoworkMetrics
    distinct_user_count: int
    office_metrics: BetaAnalyticsConnectorOfficeMetrics
    chat_cowork_unified_metrics: Optional[ChatCoworkUnifiedMetrics] = None
    connector_display_name: Optional[str] = None
    individual_auth_distinct_user_count: Optional[int] = None
    managed_auth_distinct_user_count: Optional[int] = None
    product: Optional[str] = None
    rbac_group_id: Optional[str] = None
    rbac_group_name: Optional[str] = None
    read_call_count: Optional[int] = None
    unclassified_call_count: Optional[int] = None
    user_id: Optional[str] = None
    write_call_count: Optional[int] = None
