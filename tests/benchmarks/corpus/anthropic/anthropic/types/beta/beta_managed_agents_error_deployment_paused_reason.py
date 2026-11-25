
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel
from .beta_managed_agents_deployment_paused_reason_error import BetaManagedAgentsDeploymentPausedReasonError

class BetaManagedAgentsErrorDeploymentPausedReason(BaseModel):
    """A scheduled fire recorded a failed run whose error auto-pauses the deployment."""
    error: BetaManagedAgentsDeploymentPausedReasonError
    type: Literal['error']
