
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class BetaManagedAgentsMemoryStoreResourceConfig(BaseModel):
    """A memory store attached to each session created from this deployment."""
    memory_store_id: str
    type: Literal['memory_store']
    access: Optional[Literal['read_write', 'read_only']] = None
    instructions: Optional[str] = None
