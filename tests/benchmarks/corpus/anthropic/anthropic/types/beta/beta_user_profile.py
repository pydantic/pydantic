
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Dict, Optional
from datetime import datetime
from typing_extensions import Literal
from ..._models import BaseModel
from .beta_user_profile_trust_grant import BetaUserProfileTrustGrant
from .beta_user_profile_external_user_details import BetaUserProfileExternalUserDetails

class BetaUserProfile(BaseModel):
    """
    A record of an entity that the platform serves through the API, such as an end-user of the platform's product or a company that the platform resells Claude access to.

    A Messages, Message Batches or token counting request can send a profile's `id` in the `anthropic-user-profile-id` header to attribute the request to that entity.
    """
    id: str
    created_at: datetime
    metadata: Dict[str, str]
    name: Optional[str] = None
    trust_grants: Dict[str, BetaUserProfileTrustGrant]
    type: Literal['user_profile']
    updated_at: datetime
    access_type: Optional[Literal['application', 'passthrough']] = None
    external_id: Optional[str] = None
    external_user_details: Optional[BetaUserProfileExternalUserDetails] = None
    external_user_onboarded_at: Optional[datetime] = None
