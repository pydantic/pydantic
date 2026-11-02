# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class FileCounts(BaseModel):
    cancelled: int
    completed: int
    failed: int
    in_progress: int
    total: int

class VectorStoreFileBatch(BaseModel):
    """A batch of files attached to a vector store."""
    id: str
    created_at: int
    file_counts: FileCounts
    object: Literal['vector_store.files_batch']
    status: Literal['in_progress', 'completed', 'cancelled', 'failed']
    vector_store_id: str
