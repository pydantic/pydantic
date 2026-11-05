# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class InfoEvent(BaseModel):
    """
    An informational notice about the Live session, such as the event permissions applied to a frontend data channel.
    """
    code: str
    event_id: str
    message: str
    type: Literal['info']
    client_event_id: Optional[str] = None
