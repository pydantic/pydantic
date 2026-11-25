# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from ..._models import BaseModel

class ServerEventSelector(BaseModel):
    """A Live server event selector for the WebRTC frontend data channel."""
    type: str
    response_event: Optional[str] = None
