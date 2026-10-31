
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel
from .beta_managed_agents_delta_content import BetaManagedAgentsDeltaContent

class BetaManagedAgentsDeltaEvent(BaseModel):
    """An incremental update to an event that is still being streamed.

    Deltas are best-effort and may stop early; when the buffered event with id == event_id is produced it carries the complete content. A model request that ends early (an error or interrupt) produces no buffered event — its terminal span.model_request_end closes the preview. Only sent on stream connections that opt in via event_deltas; never appears in event history.
    """
    delta: BetaManagedAgentsDeltaContent
    event_id: str
    type: Literal['event_delta']
