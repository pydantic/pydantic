
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class BetaManagedAgentsWorkspaceArchivedDeploymentPausedReasonError(BaseModel):
    """The deployment's workspace was archived."""
    type: Literal['workspace_archived_error']
