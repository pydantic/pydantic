
# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from .session import Session
from ...._models import BaseModel

class SessionUpdatedEvent(BaseModel):
    event_id: str
    session: Session
    type: Literal['session.updated']
