
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class BetaManagedAgentsSessionCreationRejectedRunError(BaseModel):
    """The session create request was rejected with a non-retryable validation error."""
    message: str
    type: Literal['session_creation_rejected_error']
