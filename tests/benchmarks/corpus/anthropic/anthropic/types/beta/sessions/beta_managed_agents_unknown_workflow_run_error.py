
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...._models import BaseModel

class BetaManagedAgentsUnknownWorkflowRunError(BaseModel):
    """A failure that has no type of its own."""
    message: str
    type: Literal['unknown_error']
