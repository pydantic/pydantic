
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from datetime import datetime
from typing_extensions import Literal
from ..._models import BaseModel

class BetaManagedAgentsScheduleTriggerContext(BaseModel):
    """The run was fired by the deployment's cron schedule."""
    scheduled_at: datetime
    type: Literal['schedule']
