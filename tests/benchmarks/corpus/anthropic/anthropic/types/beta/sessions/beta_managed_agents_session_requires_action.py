
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import List
from typing_extensions import Literal
from ...._models import BaseModel

class BetaManagedAgentsSessionRequiresAction(BaseModel):
    """
    The agent is idle waiting on one or more blocking user-input events (tool confirmation, custom tool result, etc.). Resolving all of them transitions the session back to running.
    """
    event_ids: List[str]
    type: Literal['requires_action']
