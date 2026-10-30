
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import List
from typing_extensions import Literal
from ...._models import BaseModel

class BetaManagedAgentsLimitedCredentialNetworkingResponse(BaseModel):
    """The secret is substituted only on requests to the listed hosts."""
    allowed_hosts: List[str]
    type: Literal['limited']
