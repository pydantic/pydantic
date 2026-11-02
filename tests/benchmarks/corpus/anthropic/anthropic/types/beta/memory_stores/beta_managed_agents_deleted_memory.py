
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...._models import BaseModel

class BetaManagedAgentsDeletedMemory(BaseModel):
    """
    The confirmation that [Delete a Memory](https://platform.claude.com/docs/en/api/beta/memory_stores/memories/delete) returns.

    Deleting a memory doesn't delete its versions. [List Memory Versions](https://platform.claude.com/docs/en/api/beta/memory_stores/memory_versions/list) returns them while they are retained: each version is kept for at least the version retention period after it was written, unless the store itself is deleted.

    See the [memory guide](https://platform.claude.com/docs/en/managed-agents/memory#audit-memory-changes) to learn more about how long versions are kept.
    """
    id: str
    type: Literal['memory_deleted']
