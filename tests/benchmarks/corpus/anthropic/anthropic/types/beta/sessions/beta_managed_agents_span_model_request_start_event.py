
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from datetime import datetime
from typing_extensions import Literal
from ...._models import BaseModel

class BetaManagedAgentsSpanModelRequestStartEvent(BaseModel):
    """Emitted when a model request is initiated by the agent."""
    id: str
    processed_at: datetime
    type: Literal['span.model_request_start']
