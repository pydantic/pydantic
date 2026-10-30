
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from datetime import datetime
from typing_extensions import Literal
from ...._models import BaseModel
from .beta_message_batch_request_counts import BetaMessageBatchRequestCounts

class BetaMessageBatch(BaseModel):
    id: str
    archived_at: Optional[datetime] = None
    cancel_initiated_at: Optional[datetime] = None
    created_at: datetime
    ended_at: Optional[datetime] = None
    expires_at: datetime
    processing_status: Literal['in_progress', 'canceling', 'ended']
    request_counts: BetaMessageBatchRequestCounts
    results_url: Optional[str] = None
    type: Literal['message_batch']
