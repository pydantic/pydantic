
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...._models import BaseModel

class BetaManagedAgentsThreadLimitWorkflowRunError(BaseModel):
    """The run exceeded the limit on the number of threads that a run can create."""
    message: str
    type: Literal['thread_limit_error']
