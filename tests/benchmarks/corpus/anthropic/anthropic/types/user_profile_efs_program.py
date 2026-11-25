
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Dict
from .._models import BaseModel
from .user_profile_efs_feature import UserProfileEfsFeature
from .user_profile_program_status import UserProfileProgramStatus

class UserProfileEfsProgram(BaseModel):
    """
    A user profile's standing in Enterprise Frontier Safeguards, a program under which Anthropic approves the entity the profile represents and may approve any of the program's features.
    """
    features: Dict[str, UserProfileEfsFeature]
    status: UserProfileProgramStatus
