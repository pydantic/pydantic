
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class BetaManagedAgentsMultiagentAdvisorEnabled(BaseModel):
    """The session's primary thread can consult `model` mid-turn."""
    model: str
    type: Literal['enabled']
