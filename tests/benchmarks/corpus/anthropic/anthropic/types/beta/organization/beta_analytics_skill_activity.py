
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ...._models import BaseModel
from .beta_analytics_skill_chat_metrics import BetaAnalyticsSkillChatMetrics
from .beta_analytics_skill_cowork_metrics import BetaAnalyticsSkillCoworkMetrics
from .beta_analytics_skill_office_metrics import BetaAnalyticsSkillOfficeMetrics
from .beta_analytics_skill_claude_code_metrics import BetaAnalyticsSkillClaudeCodeMetrics
from .beta_analytics_skill_chat_cowork_unified_chat_metrics import BetaAnalyticsSkillChatCoworkUnifiedChatMetrics
from .beta_analytics_skill_chat_cowork_unified_sessions_metrics import BetaAnalyticsSkillChatCoworkUnifiedSessionsMetrics

class ChatCoworkUnifiedMetrics(BaseModel):
    """
    Skill use recorded while members had Chat and Cowork unified (Cowork's features inside claude.ai chat) turned on, split into chat conversations and Cowork sessions. A count is null in date-range mode where it cannot be computed. Omitted from the response on deployments that do not offer Chat and Cowork unified.
    """
    chat: BetaAnalyticsSkillChatCoworkUnifiedChatMetrics
    sessions: BetaAnalyticsSkillChatCoworkUnifiedSessionsMetrics

class BetaAnalyticsSkillActivity(BaseModel):
    """Per-skill activity data for a given day."""
    chat_metrics: BetaAnalyticsSkillChatMetrics
    claude_code_metrics: BetaAnalyticsSkillClaudeCodeMetrics
    cowork_metrics: BetaAnalyticsSkillCoworkMetrics
    distinct_user_count: int
    office_metrics: BetaAnalyticsSkillOfficeMetrics
    skill_name: str
    attributed_list_price: Optional[str] = None
    chat_cowork_unified_metrics: Optional[ChatCoworkUnifiedMetrics] = None
    currency: Optional[str] = None
    enable_count: Optional[int] = None
    estimated_overage_spend: Optional[str] = None
    invocation_count: Optional[int] = None
    product: Optional[str] = None
    rbac_group_id: Optional[str] = None
    rbac_group_name: Optional[str] = None
    share_status: Optional[Literal['organization', 'private', 'public']] = None
    skill_display_name: Optional[str] = None
    user_id: Optional[str] = None
