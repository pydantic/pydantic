
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class BetaWebhookSessionThreadTerminatedEventData(BaseModel):
    id: str
    organization_id: str
    session_thread_id: str
    type: Literal['session.thread_terminated']
    workspace_id: str
