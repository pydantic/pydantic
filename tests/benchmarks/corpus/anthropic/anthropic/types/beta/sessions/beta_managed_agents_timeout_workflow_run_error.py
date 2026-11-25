
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...._models import BaseModel

class BetaManagedAgentsTimeoutWorkflowRunError(BaseModel):
    """The run reached its time limit."""
    message: str
    type: Literal['timeout_error']
