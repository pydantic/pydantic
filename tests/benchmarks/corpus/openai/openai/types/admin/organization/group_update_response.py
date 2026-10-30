# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from ...._models import BaseModel

class GroupUpdateResponse(BaseModel):
    """Response returned after updating a group."""
    id: str
    created_at: int
    is_scim_managed: bool
    name: str
