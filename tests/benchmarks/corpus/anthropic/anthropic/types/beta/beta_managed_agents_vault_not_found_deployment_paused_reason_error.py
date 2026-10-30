
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class BetaManagedAgentsVaultNotFoundDeploymentPausedReasonError(BaseModel):
    """A vault referenced by the deployment no longer exists."""
    type: Literal['vault_not_found_error']
