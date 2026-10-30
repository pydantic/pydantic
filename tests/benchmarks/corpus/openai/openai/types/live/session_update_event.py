# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel
from .session_update_config import SessionUpdateConfig

class SessionUpdateEvent(BaseModel):
    """Update the delegation settings or transcript triggers of an active Live session.

    The server acknowledges accepted changes with `session.updated`.
    """
    session: SessionUpdateConfig
    type: Literal['session.update']
    event_id: Optional[str] = None
