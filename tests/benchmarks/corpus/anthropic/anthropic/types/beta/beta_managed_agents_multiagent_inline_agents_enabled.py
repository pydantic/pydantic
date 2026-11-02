
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class BetaManagedAgentsMultiagentInlineAgentsEnabled(BaseModel):
    """The agent can define inline agents."""
    type: Literal['enabled']
