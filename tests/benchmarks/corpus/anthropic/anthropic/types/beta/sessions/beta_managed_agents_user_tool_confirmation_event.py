
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from datetime import datetime
from typing_extensions import Literal
from ...._models import BaseModel

class BetaManagedAgentsUserToolConfirmationEvent(BaseModel):
    """A tool confirmation event that approves or denies a pending tool execution."""
    id: str
    result: Literal['allow', 'deny']
    tool_use_id: str
    type: Literal['user.tool_confirmation']
    deny_message: Optional[str] = None
    processed_at: Optional[datetime] = None
    session_thread_id: Optional[str] = None
