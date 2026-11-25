# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class Error(BaseModel):
    """
    A description of the error that caused the response to fail,
    populated when the `status` is `failed`.
    """
    code: Optional[str] = None
    message: Optional[str] = None
    type: Optional[str] = None

class RealtimeResponseStatus(BaseModel):
    """Additional details about the status."""
    error: Optional[Error] = None
    reason: Optional[Literal['turn_detected', 'client_cancelled', 'max_output_tokens', 'content_filter']] = None
    type: Optional[Literal['completed', 'cancelled', 'incomplete', 'failed']] = None
