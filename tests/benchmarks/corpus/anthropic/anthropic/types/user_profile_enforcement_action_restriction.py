
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from datetime import datetime
from typing_extensions import Literal
from .._models import BaseModel
from .user_profile_enforcement_action_reason import UserProfileEnforcementActionReason
from .user_profile_enforcement_action_next_step import UserProfileEnforcementActionNextStep

class UserProfileEnforcementActionRestriction(BaseModel):
    """Anthropic has limited how it serves the end user until the action is resolved.

    The end user may still be served in part.
    """
    id: str
    action: Optional[UserProfileEnforcementActionNextStep] = None
    expires_at: Optional[datetime] = None
    opened_at: datetime
    reason: UserProfileEnforcementActionReason
    type: Literal['restriction']
