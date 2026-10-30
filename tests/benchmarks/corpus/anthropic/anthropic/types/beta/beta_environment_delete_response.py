
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class BetaEnvironmentDeleteResponse(BaseModel):
    """Response after deleting an environment."""
    id: str
    type: Literal['environment_deleted']
