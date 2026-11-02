# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel
from .realtime_error import RealtimeError

class RealtimeErrorEvent(BaseModel):
    """
    Returned when an error occurs, which could be a client problem or a server
    problem. Most errors are recoverable and the session will stay open, we
    recommend to implementers to monitor and log error messages by default.
    """
    error: RealtimeError
    event_id: str
    type: Literal['error']
