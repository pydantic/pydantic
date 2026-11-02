# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from ..._models import BaseModel

class SessionError(BaseModel):
    """An error payload with the same public fields as Responses API streaming errors."""
    code: Optional[str] = None
    message: str
    param: Optional[str] = None
    type: str
