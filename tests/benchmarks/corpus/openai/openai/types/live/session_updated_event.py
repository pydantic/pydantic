# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel
from .session_resource import SessionResource

class SessionUpdatedEvent(BaseModel):
    """Returned when a Live session update is accepted.

    Contains the resolved session configuration after the update.
    """
    event_id: str
    session: SessionResource
    type: Literal['session.updated']
    client_event_id: Optional[str] = None
