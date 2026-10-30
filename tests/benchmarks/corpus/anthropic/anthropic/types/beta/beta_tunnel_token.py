
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class BetaTunnelToken(BaseModel):
    """A tunnel's connector token."""
    id: str
    tunnel_token: str
    type: Literal['tunnel_token']
