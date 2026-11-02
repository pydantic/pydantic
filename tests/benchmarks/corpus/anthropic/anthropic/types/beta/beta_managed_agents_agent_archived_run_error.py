
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class BetaManagedAgentsAgentArchivedRunError(BaseModel):
    """The deployment's agent was archived."""
    message: str
    type: Literal['agent_archived_error']
