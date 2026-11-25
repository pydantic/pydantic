
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from datetime import datetime
from typing_extensions import Literal
from ...._models import BaseModel
from .beta_managed_agents_workflow_run_error import BetaManagedAgentsWorkflowRunError

class BetaManagedAgentsWorkflowRunErrorEvent(BaseModel):
    """A workflow run met an error, or an error kept a run from being created.

    A run that ends with a `result.type` of `error` emits this event before its `workflow_run.status_ended`, with the same `error`.
    """
    id: str
    error: BetaManagedAgentsWorkflowRunError
    processed_at: datetime
    type: Literal['workflow_run.error']
    workflow_run_id: Optional[str] = None
