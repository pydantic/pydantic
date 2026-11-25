
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class BetaWebhookEnvironmentCreatedEventData(BaseModel):
    id: str
    organization_id: str
    type: Literal['environment.created']
    workspace_id: str
