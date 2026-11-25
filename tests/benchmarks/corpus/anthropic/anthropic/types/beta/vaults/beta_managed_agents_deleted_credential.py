
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...._models import BaseModel

class BetaManagedAgentsDeletedCredential(BaseModel):
    """Confirmation of a deleted credential."""
    id: str
    type: Literal['vault_credential_deleted']
