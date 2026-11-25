
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class BetaWebhookDeploymentDeletedEventData(BaseModel):
    id: str
    organization_id: str
    type: Literal['deployment.deleted']
    workspace_id: str
