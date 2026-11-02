
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...._models import BaseModel

class BetaManagedAgentsTokenEndpointAuthPostResponse(BaseModel):
    """Token endpoint uses POST body authentication with client credentials."""
    type: Literal['client_secret_post']
