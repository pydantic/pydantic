
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class BetaManagedAgentsDeletedSession(BaseModel):
    """Confirmation that a `session` has been permanently deleted."""
    id: str
    type: Literal['session_deleted']
