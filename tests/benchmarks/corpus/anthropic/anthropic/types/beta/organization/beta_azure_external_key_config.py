
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ...._models import BaseModel

class BetaAzureExternalKeyConfig(BaseModel):
    key_name: str
    tenant_id: str
    type: Literal['azure']
    vault_uri: str
    client_id: Optional[str] = None
