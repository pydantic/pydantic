
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from datetime import datetime
from ...._models import BaseModel

class BetaAnalyticsSingleDayActivitySummary(BaseModel):
    """Per-day entry in the /summaries response."""
    assigned_seat_count: Optional[int] = None
    cowork_daily_active_user_count: int
    cowork_monthly_active_user_count: int
    cowork_weekly_active_user_count: int
    daily_active_user_count: int
    daily_adoption_rate: Optional[float] = None
    ending_at: datetime
    monthly_active_user_count: int
    monthly_adoption_rate: Optional[float] = None
    pending_invite_count: Optional[int] = None
    starting_at: datetime
    weekly_active_user_count: int
    weekly_adoption_rate: Optional[float] = None
    chat_cowork_unified_daily_active_user_count: Optional[int] = None
    chat_cowork_unified_monthly_active_user_count: Optional[int] = None
    chat_cowork_unified_weekly_active_user_count: Optional[int] = None
    chat_daily_active_user_count: Optional[int] = None
    chat_monthly_active_user_count: Optional[int] = None
    chat_weekly_active_user_count: Optional[int] = None
    claude_code_daily_active_user_count: Optional[int] = None
    claude_code_monthly_active_user_count: Optional[int] = None
    claude_code_weekly_active_user_count: Optional[int] = None
    claude_design_daily_active_user_count: Optional[int] = None
    claude_design_monthly_active_user_count: Optional[int] = None
    claude_design_weekly_active_user_count: Optional[int] = None
    office_agent_daily_active_user_count: Optional[int] = None
    office_agent_monthly_active_user_count: Optional[int] = None
    office_agent_weekly_active_user_count: Optional[int] = None
    science_daily_active_user_count: Optional[int] = None
    science_entitled_user_count: Optional[int] = None
    science_monthly_active_user_count: Optional[int] = None
    science_weekly_active_user_count: Optional[int] = None
