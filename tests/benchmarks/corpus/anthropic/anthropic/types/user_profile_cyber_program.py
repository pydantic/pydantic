
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Dict, Optional
from .._models import BaseModel
from .user_profile_cyber_tier import UserProfileCyberTier
from .user_profile_program_status import UserProfileProgramStatus
from .user_profile_cyber_requirements import UserProfileCyberRequirements

class UserProfileCyberProgram(BaseModel):
    """
    A user profile's standing in the Cyber Verification Program, which relaxes cyber safeguards for requests that name the profile.
    """
    requirements: Optional[UserProfileCyberRequirements] = None
    status: UserProfileProgramStatus
    tiers: Dict[str, UserProfileCyberTier]
