
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class BetaWebhookAgentDeletedEventData(BaseModel):
    id: str
    organization_id: str
    type: Literal['agent.deleted']
    workspace_id: str
