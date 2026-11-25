# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel
from .session_resource import SessionResource

class SessionStartedEvent(BaseModel):
    """Returned when a Live session has started.

    Contains the resolved session configuration, including server defaults.
    """
    event_id: str
    session: SessionResource
    type: Literal['session.started']
    client_event_id: Optional[str] = None
