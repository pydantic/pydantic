
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Dict, List, Optional
from datetime import datetime
from typing_extensions import Literal
from .._models import BaseModel
from .user_profile_programs import UserProfilePrograms
from .user_profile_access_type import UserProfileAccessType
from .user_profile_enforcement_action import UserProfileEnforcementAction
from .user_profile_enforcement_status import UserProfileEnforcementStatus
from .user_profile_external_user_details import UserProfileExternalUserDetails

class UserProfile(BaseModel):
    """
    A record of an entity that the platform serves through the API, such as an end-user of the platform's product or a company that the platform resells Claude access to.

    A Messages, Message Batches or token counting request can send a profile's `id` in the `anthropic-user-profile-id` header to attribute the request to that entity.
    """
    id: str
    access_type: UserProfileAccessType
    created_at: datetime
    enforcement_actions: List[UserProfileEnforcementAction]
    enforcement_status: UserProfileEnforcementStatus
    external_user_details: UserProfileExternalUserDetails
    metadata: Dict[str, str]
    name: Optional[str] = None
    programs: UserProfilePrograms
    type: Literal['user_profile']
    updated_at: datetime
