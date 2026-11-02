
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from datetime import datetime
from typing_extensions import Literal
from ...._models import BaseModel

class BetaManagedAgentsMemory(BaseModel):
    """A text document at a path inside a memory store.

    `content` is `null` when the response uses `view=basic`. `content_size_bytes` and `content_sha256` are always set, so you can detect changes without fetching the content. To retrieve, update, or delete a memory, pass its ID, which stays the same when its path changes.

    See the [memory guide](https://platform.claude.com/docs/en/managed-agents/memory#view-and-edit-memories) to learn more about working with memories.
    """
    id: str
    content_sha256: str
    content_size_bytes: int
    created_at: datetime
    memory_store_id: str
    memory_version_id: str
    path: str
    type: Literal['memory']
    updated_at: datetime
    content: Optional[str] = None
