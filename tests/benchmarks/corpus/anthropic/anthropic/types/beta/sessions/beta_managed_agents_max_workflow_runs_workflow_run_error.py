
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...._models import BaseModel

class BetaManagedAgentsMaxWorkflowRunsWorkflowRunError(BaseModel):
    """
    No run was created, because the session was at its limit of open workflow runs, which are runs that have not ended. Only `workflow_run.error` carries this type.
    """
    message: str
    type: Literal['max_workflow_runs_error']
