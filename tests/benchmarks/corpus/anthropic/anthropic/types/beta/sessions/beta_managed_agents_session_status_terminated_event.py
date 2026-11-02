
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from datetime import datetime
from typing_extensions import Literal
from ...._models import BaseModel

class BetaManagedAgentsSessionStatusTerminatedEvent(BaseModel):
    """Indicates the session has terminated, either due to an error or completion."""
    id: str
    processed_at: datetime
    type: Literal['session.status_terminated']
