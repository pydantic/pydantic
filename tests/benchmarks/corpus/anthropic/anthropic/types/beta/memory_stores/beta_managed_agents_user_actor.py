
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...._models import BaseModel

class BetaManagedAgentsUserActor(BaseModel):
    """A human user, for example acting through the Anthropic Console."""
    type: Literal['user_actor']
    user_id: str
