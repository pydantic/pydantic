
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from ...._models import BaseModel

class BetaOrganizationWebhookEndpointSigningSecret(BaseModel):
    """An organization webhook endpoint's new signing secret."""
    signing_secret: str
