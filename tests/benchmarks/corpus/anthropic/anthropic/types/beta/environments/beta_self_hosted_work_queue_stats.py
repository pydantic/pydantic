
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ...._models import BaseModel

class BetaSelfHostedWorkQueueStats(BaseModel):
    """Statistics about the work queue for an environment."""
    depth: int
    oldest_queued_at: Optional[str] = None
    pending: int
    type: Literal['work_queue_stats']
    workers_polling: Optional[int] = None
