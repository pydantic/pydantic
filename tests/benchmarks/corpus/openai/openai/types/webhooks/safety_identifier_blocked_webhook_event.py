
# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class Data(BaseModel):
    """Event data payload."""
    safety_category: str
    safety_identifier: str
    model: Optional[str] = None
    project_id: Optional[str] = None
    request_id: Optional[str] = None

class SafetyIdentifierBlockedWebhookEvent(BaseModel):
    """Sent when a request associated with a safety identifier has been blocked."""
    id: str
    created_at: int
    data: Data
    type: Literal['safety_identifier.blocked']
    object: Optional[Literal['event']] = None
