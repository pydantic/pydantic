
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...._models import BaseModel

class BetaManagedAgentsSessionActor(BaseModel):
    """
    An agent acting during a session, for example through the session's mounted filesystem. It names the session itself, not the user or API key that started the session.
    """
    session_id: str
    type: Literal['session_actor']
