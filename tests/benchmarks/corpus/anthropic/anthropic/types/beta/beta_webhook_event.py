
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from datetime import datetime
from typing_extensions import Literal
from ..._models import BaseModel
from .beta_webhook_event_data import BetaWebhookEventData

class BetaWebhookEvent(BaseModel):
    id: str
    created_at: datetime
    data: BetaWebhookEventData
    type: Literal['event']
