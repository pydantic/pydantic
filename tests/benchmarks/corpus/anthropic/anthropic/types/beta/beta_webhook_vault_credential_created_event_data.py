
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class BetaWebhookVaultCredentialCreatedEventData(BaseModel):
    id: str
    organization_id: str
    type: Literal['vault_credential.created']
    vault_id: str
    workspace_id: str
