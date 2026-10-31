
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from datetime import datetime
from typing_extensions import Literal
from ...._models import BaseModel

class BetaManagedAgentsSessionStatusRescheduledEvent(BaseModel):
    """
    Indicates the session is recovering from an error state and is rescheduled for execution.
    """
    id: str
    processed_at: datetime
    type: Literal['session.status_rescheduled']
