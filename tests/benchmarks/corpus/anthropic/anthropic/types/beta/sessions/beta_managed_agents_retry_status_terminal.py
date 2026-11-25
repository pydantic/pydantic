
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...._models import BaseModel

class BetaManagedAgentsRetryStatusTerminal(BaseModel):
    """
    The session encountered a terminal error and will transition to `terminated` state.
    """
    type: Literal['terminal']
