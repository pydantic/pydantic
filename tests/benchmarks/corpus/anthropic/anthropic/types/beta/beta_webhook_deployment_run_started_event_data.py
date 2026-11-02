
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class BetaWebhookDeploymentRunStartedEventData(BaseModel):
    id: str
    organization_id: str
    type: Literal['deployment_run.started']
    workspace_id: str
