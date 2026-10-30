
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class BetaManagedAgentsFileNotFoundDeploymentPausedReasonError(BaseModel):
    """A file resource referenced by the deployment no longer exists."""
    type: Literal['file_not_found_error']
