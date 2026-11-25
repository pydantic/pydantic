
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class BetaManagedAgentsAdvisor(BaseModel):
    """
    Platform advisor roster entry: a model the session's primary thread may consult mid-turn.
    """
    model: str
    type: Literal['advisor']
