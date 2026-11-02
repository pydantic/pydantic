
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class BetaManagedAgentsMemoryStoreArchivedRunError(BaseModel):
    """A memory store referenced by the deployment is archived."""
    message: str
    type: Literal['memory_store_archived_error']
