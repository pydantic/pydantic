# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class UploadPart(BaseModel):
    """The upload Part represents a chunk of bytes we can add to an Upload object."""
    id: str
    created_at: int
    object: Literal['upload.part']
    upload_id: str
