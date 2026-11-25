
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...._models import BaseModel

class BetaManagedAgentsUnrestrictedCredentialNetworkingResponse(BaseModel):
    """
    The secret is substituted on any host the session's Environment network policy permits egress to.
    """
    type: Literal['unrestricted']
