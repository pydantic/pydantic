# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class FileRetrieveResponse(BaseModel):
    id: str
    bytes: int
    container_id: str
    created_at: int
    object: Literal['container.file']
    path: str
    source: str
