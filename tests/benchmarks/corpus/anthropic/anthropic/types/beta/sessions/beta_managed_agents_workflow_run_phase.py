
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from ...._models import BaseModel

class BetaManagedAgentsWorkflowRunPhase(BaseModel):
    """A phase that a workflow run's plan declares."""
    id: str
    description: Optional[str] = None
    name: str
