
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from datetime import datetime
from typing_extensions import Literal
from ...._models import BaseModel

class BetaManagedAgentsUserInterruptEvent(BaseModel):
    """An interrupt event that pauses agent execution and returns control to the user."""
    id: str
    type: Literal['user.interrupt']
    processed_at: Optional[datetime] = None
    session_thread_id: Optional[str] = None
