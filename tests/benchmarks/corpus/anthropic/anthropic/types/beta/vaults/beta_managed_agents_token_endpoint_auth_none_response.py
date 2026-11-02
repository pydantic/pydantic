
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...._models import BaseModel

class BetaManagedAgentsTokenEndpointAuthNoneResponse(BaseModel):
    """Token endpoint requires no client authentication."""
    type: Literal['none']
