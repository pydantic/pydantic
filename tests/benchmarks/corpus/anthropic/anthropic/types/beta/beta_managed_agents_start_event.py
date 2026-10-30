
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel
from .beta_managed_agents_start_event_preview import BetaManagedAgentsStartEventPreview

class BetaManagedAgentsStartEvent(BaseModel):
    """Opens a preview of a buffered event.

    Carries the previewed event's type and id only. Followed by zero or more event_delta events with the same event id, normally concluded by the buffered event carrying that id. If the producing model request ends without that event (an error or interrupt mid-stream), its terminal span.model_request_end closes the preview. Only sent on stream connections that opt in via event_deltas; never appears in event history.
    """
    event: BetaManagedAgentsStartEventPreview
    type: Literal['event_start']
