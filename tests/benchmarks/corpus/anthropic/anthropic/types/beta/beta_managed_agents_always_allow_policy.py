
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class BetaManagedAgentsAlwaysAllowPolicy(BaseModel):
    """Tool calls are automatically approved without user confirmation."""
    type: Literal['always_allow']
