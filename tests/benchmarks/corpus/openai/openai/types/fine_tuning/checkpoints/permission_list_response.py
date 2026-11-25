# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...._models import BaseModel

class PermissionListResponse(BaseModel):
    """
    The `checkpoint.permission` object represents a permission for a fine-tuned model checkpoint.
    """
    id: str
    created_at: int
    object: Literal['checkpoint.permission']
    project_id: str
