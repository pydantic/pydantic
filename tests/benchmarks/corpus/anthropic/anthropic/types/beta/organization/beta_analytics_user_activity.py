
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from datetime import date
from ...._models import BaseModel
from .beta_analytics_user import BetaAnalyticsUser
from .beta_analytics_chat_metrics import BetaAnalyticsChatMetrics
from .beta_analytics_cowork_metrics import BetaAnalyticsCoworkMetrics
from .beta_analytics_design_metrics import BetaAnalyticsDesignMetrics
from .beta_analytics_office_metrics import BetaAnalyticsOfficeMetrics
from .beta_analytics_science_metrics import BetaAnalyticsScienceMetrics
from .beta_analytics_claude_code_metrics import BetaAnalyticsClaudeCodeMetrics
from .beta_analytics_chat_cowork_unified_chat_metrics import BetaAnalyticsChatCoworkUnifiedChatMetrics
from .beta_analytics_chat_cowork_unified_sessions_metrics import BetaAnalyticsChatCoworkUnifiedSessionsMetrics

class ChatCoworkUnifiedMetrics(BaseModel):
    """
    Activity recorded while the member had Chat and Cowork unified (Cowork's features inside claude.ai chat) turned on, split into `chat` (chat activity) and `sessions` (Cowork activity). Omitted from the response on deployments that do not offer Chat and Cowork unified.
    """
    chat: BetaAnalyticsChatCoworkUnifiedChatMetrics
    sessions: BetaAnalyticsChatCoworkUnifiedSessionsMetrics

class BetaAnalyticsUserActivity(BaseModel):
    """Per-user activity data for a given day."""
    chat_metrics: BetaAnalyticsChatMetrics
    claude_code_metrics: BetaAnalyticsClaudeCodeMetrics
    cowork_metrics: BetaAnalyticsCoworkMetrics
    design_metrics: BetaAnalyticsDesignMetrics
    office_metrics: BetaAnalyticsOfficeMetrics
    science_metrics: BetaAnalyticsScienceMetrics
    web_search_count: int
    chat_cowork_unified_metrics: Optional[ChatCoworkUnifiedMetrics] = None
    distinct_user_count: Optional[int] = None
    last_activity_date: Optional[date] = None
    rbac_group_id: Optional[str] = None
    rbac_group_name: Optional[str] = None
    user: Optional[BetaAnalyticsUser] = None
