
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ...._models import BaseModel

class BetaManagedAgentsMemoryStoreResource(BaseModel):
    """A memory store attached to an agent session."""
    memory_store_id: str
    type: Literal['memory_store']
    access: Optional[Literal['read_write', 'read_only']] = None
    description: Optional[str] = None
    instructions: Optional[str] = None
    mount_path: Optional[str] = None
    name: Optional[str] = None
