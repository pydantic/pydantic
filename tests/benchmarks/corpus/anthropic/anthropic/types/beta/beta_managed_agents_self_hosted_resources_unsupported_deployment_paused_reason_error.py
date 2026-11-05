
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class BetaManagedAgentsSelfHostedResourcesUnsupportedDeploymentPausedReasonError(BaseModel):
    """
    The deployment configures resources, but its environment is self-hosted and cannot mount them.
    """
    type: Literal['self_hosted_resources_unsupported_error']
