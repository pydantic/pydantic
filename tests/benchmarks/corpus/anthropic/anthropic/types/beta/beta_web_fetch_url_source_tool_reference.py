
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class BetaWebFetchURLSourceToolReference(BaseModel):
    """
    One entry of a tool filter's ``tools``: it must name a tool declared
    in this request's ``tools[]``.
    """
    name: str
    type: Literal['tool_reference']
