# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class ThinkingAppendedEvent(BaseModel):
    """
    Returned when a session.thinking.append command is accepted into the Live session timeline. Acknowledges the added reasoning context without guaranteeing any spoken output.
    """
    end_ms: int
    event_id: str
    start_ms: int
    type: Literal['session.thinking.appended']
    client_event_id: Optional[str] = None
