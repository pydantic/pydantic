
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class BetaManagedAgentsOrganizationDisabledDeploymentPausedReasonError(BaseModel):
    """The deployment's organization is disabled."""
    type: Literal['organization_disabled_error']
