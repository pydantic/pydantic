
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class BetaManagedAgentsMemoryStoreArchivedDeploymentPausedReasonError(BaseModel):
    """A memory store referenced by the deployment is archived."""
    type: Literal['memory_store_archived_error']
