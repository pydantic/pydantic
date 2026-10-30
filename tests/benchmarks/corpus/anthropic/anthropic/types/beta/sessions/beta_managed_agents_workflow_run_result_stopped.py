
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...._models import BaseModel

class BetaManagedAgentsWorkflowRunResultStopped(BaseModel):
    """The agent stopped the run."""
    type: Literal['stopped']
