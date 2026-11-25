
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class BetaWebhookVaultCreatedEventData(BaseModel):
    id: str
    organization_id: str
    type: Literal['vault.created']
    workspace_id: str
