
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from datetime import datetime
from typing_extensions import Literal
from ...._compat import ConfigDict
from ...._models import BaseModel
from .beta_managed_agents_span_model_usage import BetaManagedAgentsSpanModelUsage

class BetaManagedAgentsSpanModelRequestEndEvent(BaseModel):
    """Emitted when a model request completes."""
    id: str
    is_error: Optional[bool] = None
    model_request_start_id: str
    model_usage: BetaManagedAgentsSpanModelUsage
    processed_at: datetime
    type: Literal['span.model_request_end']
    model_config = ConfigDict(protected_namespaces=tuple())
