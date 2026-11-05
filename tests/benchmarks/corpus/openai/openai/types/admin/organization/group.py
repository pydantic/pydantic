# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...._models import BaseModel

class Group(BaseModel):
    """Details about an organization group."""
    id: str
    created_at: int
    group_type: Literal['group', 'tenant_group']
    is_scim_managed: bool
    name: str
