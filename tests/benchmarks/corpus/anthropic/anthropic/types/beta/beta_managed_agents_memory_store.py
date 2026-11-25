
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Dict, Optional
from datetime import datetime
from typing_extensions import Literal
from ..._models import BaseModel

class BetaManagedAgentsMemoryStore(BaseModel):
    """A `memory_store`: a named container for agent memories, scoped to a workspace.

    Attach a store to a session via `resources[]` to mount it as a directory the agent can read and write.
    """
    id: str
    archived_at: Optional[datetime] = None
    created_at: datetime
    description: str
    metadata: Dict[str, str]
    name: str
    type: Literal['memory_store']
    updated_at: datetime
