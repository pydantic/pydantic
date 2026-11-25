
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class BetaWebhookDeploymentUnpausedEventData(BaseModel):
    id: str
    organization_id: str
    type: Literal['deployment.unpaused']
    workspace_id: str
