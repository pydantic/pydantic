
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from datetime import datetime
from typing_extensions import Literal
from .._models import BaseModel
from .user_profile_enforcement_action_reason import UserProfileEnforcementActionReason
from .user_profile_enforcement_action_next_step import UserProfileEnforcementActionNextStep

class UserProfileEnforcementActionBan(BaseModel):
    """
    Anthropic has stopped serving the end user where the ban applies and does not plan to serve them there again.
    """
    id: str
    action: Optional[UserProfileEnforcementActionNextStep] = None
    expires_at: Optional[datetime] = None
    opened_at: datetime
    reason: UserProfileEnforcementActionReason
    type: Literal['ban']
