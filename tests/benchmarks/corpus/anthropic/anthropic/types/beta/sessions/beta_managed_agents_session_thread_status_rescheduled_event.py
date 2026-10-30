
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from datetime import datetime
from typing_extensions import Literal
from ...._models import BaseModel

class BetaManagedAgentsSessionThreadStatusRescheduledEvent(BaseModel):
    """A session thread hit a transient error and is retrying automatically.

    Emitted on the thread's own stream and cross-posted to the primary stream for child threads.
    """
    id: str
    agent_name: str
    processed_at: datetime
    session_thread_id: str
    type: Literal['session.thread_status_rescheduled']
