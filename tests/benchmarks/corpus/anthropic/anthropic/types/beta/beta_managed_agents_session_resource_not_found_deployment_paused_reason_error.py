
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class BetaManagedAgentsSessionResourceNotFoundDeploymentPausedReasonError(BaseModel):
    """A referenced resource no longer exists and its kind was not reported."""
    type: Literal['session_resource_not_found_error']
