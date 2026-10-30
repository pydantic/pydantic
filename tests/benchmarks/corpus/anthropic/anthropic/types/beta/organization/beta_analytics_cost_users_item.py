
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from datetime import datetime
from typing_extensions import Literal
from ...._models import BaseModel
from .beta_analytics_cost_type import BetaAnalyticsCostType
from .beta_analytics_token_type import BetaAnalyticsTokenType
from .beta_analytics_user_actor import BetaAnalyticsUserActor
from .beta_analytics_context_window import BetaAnalyticsContextWindow
from .beta_analytics_claude_tag_category import BetaAnalyticsClaudeTagCategory

class BetaAnalyticsCostUsersItem(BaseModel):
    actor: BetaAnalyticsUserActor
    amount: str
    claude_tag_category: Optional[BetaAnalyticsClaudeTagCategory] = None
    claude_tag_user_id: Optional[str] = None
    context_window: Optional[BetaAnalyticsContextWindow] = None
    cost_type: Optional[BetaAnalyticsCostType] = None
    currency: str
    ending_at: Optional[datetime] = None
    inference_geo: Optional[Literal['global', 'us']] = None
    list_amount: str
    model: Optional[str] = None
    product: Optional[str] = None
    rbac_group_id: Optional[str] = None
    requests: Optional[int] = None
    slack_channel_id: Optional[str] = None
    speed: Optional[Literal['fast', 'standard']] = None
    starting_at: Optional[datetime] = None
    token_type: Optional[BetaAnalyticsTokenType] = None
