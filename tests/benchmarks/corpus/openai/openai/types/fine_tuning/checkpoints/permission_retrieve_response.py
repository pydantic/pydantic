# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Optional
from typing_extensions import Literal
from ...._models import BaseModel

class Data(BaseModel):
    """
    The `checkpoint.permission` object represents a permission for a fine-tuned model checkpoint.
    """
    id: str
    created_at: int
    object: Literal['checkpoint.permission']
    project_id: str

class PermissionRetrieveResponse(BaseModel):
    data: List[Data]
    has_more: bool
    object: Literal['list']
    first_id: Optional[str] = None
    last_id: Optional[str] = None
