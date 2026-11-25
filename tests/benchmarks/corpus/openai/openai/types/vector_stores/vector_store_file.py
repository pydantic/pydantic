# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Dict, Union, Optional
from typing_extensions import Literal
from ..._models import BaseModel
from ..file_chunking_strategy import FileChunkingStrategy

class LastError(BaseModel):
    """The last error associated with this vector store file.

    Will be `null` if there are no errors.
    """
    code: Literal['server_error', 'unsupported_file', 'invalid_file']
    message: str

class VectorStoreFile(BaseModel):
    """A list of files attached to a vector store."""
    id: str
    created_at: int
    last_error: Optional[LastError] = None
    object: Literal['vector_store.file']
    status: Literal['in_progress', 'completed', 'cancelled', 'failed']
    usage_bytes: int
    vector_store_id: str
    attributes: Optional[Dict[str, Union[str, float, bool]]] = None
    chunking_strategy: Optional[FileChunkingStrategy] = None
