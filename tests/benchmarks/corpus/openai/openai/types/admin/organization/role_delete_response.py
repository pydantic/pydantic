# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...._models import BaseModel

class RoleDeleteResponse(BaseModel):
    """Confirmation payload returned after deleting a role."""
    id: str
    deleted: bool
    object: Literal['role.deleted']
