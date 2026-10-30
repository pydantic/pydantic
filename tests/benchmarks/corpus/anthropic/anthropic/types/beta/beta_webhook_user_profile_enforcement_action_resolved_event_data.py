
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class BetaWebhookUserProfileEnforcementActionResolvedEventData(BaseModel):
    id: str
    enforcement_action_id: str
    organization_id: str
    type: Literal['user_profile.enforcement_action_resolved']
