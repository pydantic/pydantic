
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class BetaManagedAgentsEnvironmentArchivedDeploymentPausedReasonError(BaseModel):
    """The deployment's environment was archived."""
    type: Literal['environment_archived_error']
