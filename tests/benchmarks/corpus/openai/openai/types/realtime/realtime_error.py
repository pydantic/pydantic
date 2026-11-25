# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from ..._models import BaseModel

class RealtimeError(BaseModel):
    """Details of the error."""
    message: str
    type: str
    code: Optional[str] = None
    event_id: Optional[str] = None
    param: Optional[str] = None
