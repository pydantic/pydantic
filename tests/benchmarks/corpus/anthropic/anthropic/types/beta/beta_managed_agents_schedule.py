
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import List, Optional
from datetime import datetime
from typing_extensions import Literal
from ..._models import BaseModel

class BetaManagedAgentsSchedule(BaseModel):
    """A recurring schedule with computed runtime timestamps.

    Discriminated union — only cron is supported currently.
    """
    expression: str
    timezone: str
    type: Literal['cron']
    last_run_at: Optional[datetime] = None
    upcoming_runs_at: Optional[List[datetime]] = None
