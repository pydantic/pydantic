
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from datetime import datetime
from ...._models import BaseModel
from .beta_analytics_user import BetaAnalyticsUser

class BetaAnalyticsProjectActivity(BaseModel):
    """Per-project activity data for a given day."""
    distinct_user_count: int
    message_count: int
    project_id: str
    project_name: str
    created_at: Optional[datetime] = None
    created_by: Optional[BetaAnalyticsUser] = None
    distinct_conversation_count: Optional[int] = None
    product: Optional[str] = None
    rbac_group_id: Optional[str] = None
    rbac_group_name: Optional[str] = None
    user_id: Optional[str] = None
