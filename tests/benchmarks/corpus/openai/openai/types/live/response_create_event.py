# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class ResponseCreateEvent(BaseModel):
    """
    Request a response from the Live session’s Responses backend, or continue a delegated response waiting for tool results. Requires Responses delegation.
    """
    type: Literal['response.create']
    event_id: Optional[str] = None
