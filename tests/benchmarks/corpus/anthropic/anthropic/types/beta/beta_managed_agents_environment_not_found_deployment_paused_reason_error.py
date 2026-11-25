
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class BetaManagedAgentsEnvironmentNotFoundDeploymentPausedReasonError(BaseModel):
    """The deployment's environment no longer exists."""
    type: Literal['environment_not_found_error']
