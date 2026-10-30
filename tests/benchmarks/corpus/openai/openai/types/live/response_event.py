# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Dict, Optional
from typing_extensions import Literal
from ..._models import BaseModel

class ResponseEvent(BaseModel):
    """A streaming Responses API event from a backend delegated to by the Live session.

    Use the outer delegation_id to associate the nested stream with its Live delegation.
    """
    event: Dict[str, object]
    event_id: str
    type: Literal['response.event']
    client_event_id: Optional[str] = None
    delegation_id: Optional[str] = None
