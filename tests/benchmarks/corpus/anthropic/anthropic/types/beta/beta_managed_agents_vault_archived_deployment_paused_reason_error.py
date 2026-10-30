
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class BetaManagedAgentsVaultArchivedDeploymentPausedReasonError(BaseModel):
    """A vault referenced by the deployment is archived."""
    type: Literal['vault_archived_error']
