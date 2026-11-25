
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class BetaManagedAgentsDeletedMemoryStore(BaseModel):
    """Confirmation that a `memory_store` was deleted."""
    id: str
    type: Literal['memory_store_deleted']
