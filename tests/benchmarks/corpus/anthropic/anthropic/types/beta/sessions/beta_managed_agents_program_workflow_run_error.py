
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...._models import BaseModel

class BetaManagedAgentsProgramWorkflowRunError(BaseModel):
    """The plan, a program that the agent wrote, failed, or the server refused it."""
    message: str
    type: Literal['program_error']
