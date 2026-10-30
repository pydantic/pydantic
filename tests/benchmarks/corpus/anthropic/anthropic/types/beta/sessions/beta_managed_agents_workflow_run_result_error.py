
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...._models import BaseModel
from .beta_managed_agents_workflow_run_error import BetaManagedAgentsWorkflowRunError

class BetaManagedAgentsWorkflowRunResultError(BaseModel):
    """The run failed or reached its time limit."""
    error: BetaManagedAgentsWorkflowRunError
    type: Literal['error']
