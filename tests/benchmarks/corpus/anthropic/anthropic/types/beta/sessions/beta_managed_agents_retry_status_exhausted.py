
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...._models import BaseModel

class BetaManagedAgentsRetryStatusExhausted(BaseModel):
    """This turn is dead; queued inputs are flushed and the session returns to idle.

    Client may send a new prompt.
    """
    type: Literal['exhausted']
