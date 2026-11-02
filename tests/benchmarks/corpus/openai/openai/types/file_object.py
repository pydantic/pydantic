# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from .._models import BaseModel

class FileObject(BaseModel):
    """The `File` object represents a document that has been uploaded to OpenAI."""
    id: str
    bytes: int
    created_at: int
    filename: str
    object: Literal['file']
    purpose: Literal['assistants', 'assistants_output', 'batch', 'batch_output', 'fine-tune', 'fine-tune-results', 'vision', 'user_data']
    status: Literal['uploaded', 'processed', 'error']
    expires_at: Optional[int] = None
    status_details: Optional[str] = None
