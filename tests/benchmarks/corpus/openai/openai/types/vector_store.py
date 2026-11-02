# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from .._models import BaseModel
from .shared.metadata import Metadata

class FileCounts(BaseModel):
    cancelled: int
    completed: int
    failed: int
    in_progress: int
    total: int

class ExpiresAfter(BaseModel):
    """The expiration policy for a vector store."""
    anchor: Literal['last_active_at']
    days: int

class VectorStore(BaseModel):
    """
    A vector store is a collection of processed files can be used by the `file_search` tool.
    """
    id: str
    created_at: int
    file_counts: FileCounts
    last_active_at: Optional[int] = None
    metadata: Optional[Metadata] = None
    name: str
    object: Literal['vector_store']
    status: Literal['expired', 'in_progress', 'completed']
    usage_bytes: int
    expires_after: Optional[ExpiresAfter] = None
    expires_at: Optional[int] = None
