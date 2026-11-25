
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from datetime import datetime
from typing_extensions import Literal
from ...._models import BaseModel

class BetaManagedAgentsSessionDeletedEvent(BaseModel):
    """Emitted when a session has been deleted.

    Terminates any active event stream — no further events will be emitted for this session.
    """
    id: str
    processed_at: datetime
    type: Literal['session.deleted']
