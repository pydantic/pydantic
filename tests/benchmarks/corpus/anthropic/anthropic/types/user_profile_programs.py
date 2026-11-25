
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from .._models import BaseModel
from .user_profile_efs_program import UserProfileEfsProgram
from .user_profile_cyber_program import UserProfileCyberProgram

class UserProfilePrograms(BaseModel):
    """A user profile's standing in each program.

    A program is a set of capabilities or exemptions that Anthropic approves for the entity the profile represents. A program reads `null` when the profile has no status in it, when the caller's organization is not entitled to read programs, or when the response does not report that program. Retrieving the profile reports every program. Anthropic may add programs; ignore a key you do not recognize.
    """
    cyber: Optional[UserProfileCyberProgram] = None
    efs: Optional[UserProfileEfsProgram] = None
