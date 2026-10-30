# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from .error import Error
from ..._models import BaseModel

class ErrorEvent(BaseModel):
    """Reports an error in the Live session, such as an invalid client command.

    Use error.client_event_id, when present, to identify the command that caused the error.
    """
    error: Error
    event_id: str
    type: Literal['error']
    client_event_id: Optional[str] = None
