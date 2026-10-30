# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class Data(BaseModel):
    """Event data payload."""
    id: str

class BatchFailedWebhookEvent(BaseModel):
    """Sent when a batch API request has failed."""
    id: str
    created_at: int
    data: Data
    type: Literal['batch.failed']
    object: Optional[Literal['event']] = None
