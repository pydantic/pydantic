
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from datetime import datetime
from typing_extensions import Literal
from ...._models import BaseModel

class BetaManagedAgentsSessionThreadCreatedEvent(BaseModel):
    """Emitted when a child thread is created.

    Written to the parent thread's output stream so clients observing the session see child creation.
    """
    id: str
    agent_name: str
    processed_at: datetime
    session_thread_id: str
    type: Literal['session.thread_created']
    workflow_run_id: Optional[str] = None
