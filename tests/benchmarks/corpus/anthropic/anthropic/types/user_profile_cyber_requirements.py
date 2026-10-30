
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from .._models import BaseModel

class UserProfileCyberRequirements(BaseModel):
    """
    What a request that names the profile must allow to get the relaxed safeguards of the profile's `active` tiers. A field reads `true` when at least one of those tiers has the requirement and Anthropic has not waived it on that tier for the profile. A request that does not meet a requirement is still served, without the relaxed safeguards of the tiers that have it. The values differ between profiles and can change, so read them rather than assuming them.
    """
    data_retention: bool
    human_review: bool
