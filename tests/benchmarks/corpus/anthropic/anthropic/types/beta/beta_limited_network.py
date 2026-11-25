
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import List
from typing_extensions import Literal
from ..._models import BaseModel

class BetaLimitedNetwork(BaseModel):
    """Limited network access."""
    allow_mcp_servers: bool
    allow_package_managers: bool
    allowed_hosts: List[str]
    type: Literal['limited']
