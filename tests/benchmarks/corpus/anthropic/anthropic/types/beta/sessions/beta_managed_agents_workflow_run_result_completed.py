
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...._models import BaseModel

class BetaManagedAgentsWorkflowRunResultCompleted(BaseModel):
    """The run's plan, a program that the agent wrote, finished.

    This does not say whether the work succeeded.
    """
    type: Literal['completed']
