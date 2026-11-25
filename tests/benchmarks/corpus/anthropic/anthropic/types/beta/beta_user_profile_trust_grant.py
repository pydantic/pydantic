
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class BetaUserProfileTrustGrant(BaseModel):
    """
    The status of one trust grant on a user profile, listed in the profile's `trust_grants` map under the grant's name.
    """
    status: Literal['active', 'pending', 'rejected']
