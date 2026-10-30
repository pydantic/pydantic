# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from .._models import BaseModel
from .file_object import FileObject

class Upload(BaseModel):
    """The Upload object can accept byte chunks in the form of Parts."""
    id: str
    bytes: int
    created_at: int
    expires_at: int
    filename: str
    object: Literal['upload']
    purpose: str
    status: Literal['pending', 'completed', 'cancelled', 'expired']
    file: Optional[FileObject] = None
