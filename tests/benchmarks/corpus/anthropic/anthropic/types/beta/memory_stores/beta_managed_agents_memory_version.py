
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from datetime import datetime
from typing_extensions import Literal
from ...._models import BaseModel
from .beta_managed_agents_actor import BetaManagedAgentsActor
from .beta_managed_agents_memory_version_operation import BetaManagedAgentsMemoryVersionOperation

class BetaManagedAgentsMemoryVersion(BaseModel):
    """One entry in a memory's history, recording a single change and who made it.

    Every change to a memory adds one version. Only redaction can change a version after that. Versions belong to the memory store and stay after the memory is deleted. Each version is retained for at least the version retention period after it was written, unless the store itself is deleted.

    Retrieving a redacted version succeeds, with `content`, `path`, `content_size_bytes`, and `content_sha256` set to `null`. Check `redacted_at` to find out whether a version was redacted.

    See the [memory guide](https://platform.claude.com/docs/en/managed-agents/memory#audit-memory-changes) to learn more about memory versions.
    """
    id: str
    created_at: datetime
    memory_id: str
    memory_store_id: str
    operation: BetaManagedAgentsMemoryVersionOperation
    type: Literal['memory_version']
    content: Optional[str] = None
    content_sha256: Optional[str] = None
    content_size_bytes: Optional[int] = None
    created_by: Optional[BetaManagedAgentsActor] = None
    path: Optional[str] = None
    redacted_at: Optional[datetime] = None
    redacted_by: Optional[BetaManagedAgentsActor] = None
