
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import List
from datetime import datetime
from typing_extensions import Literal
from ...._models import BaseModel
from .beta_organization_webhook_endpoint_state import BetaOrganizationWebhookEndpointState

class BetaNewOrganizationWebhookEndpoint(BaseModel):
    """A new organization webhook endpoint, with its signing secret."""
    id: str
    created_at: datetime
    description: str
    disabled_reason: str
    enabled_events: List[Literal['user_profile.enforcement_action_opened', 'user_profile.enforcement_action_resolved']]
    name: str
    signing_secret: str
    state: BetaOrganizationWebhookEndpointState
    updated_at: datetime
    url: str
