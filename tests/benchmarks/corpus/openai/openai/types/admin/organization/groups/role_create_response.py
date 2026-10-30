# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..role import Role
from ....._models import BaseModel

class Group(BaseModel):
    """Summary information about a group returned in role assignment responses."""
    id: str
    created_at: int
    name: str
    object: Literal['group']
    scim_managed: bool

class RoleCreateResponse(BaseModel):
    """Role assignment linking a group to a role."""
    group: Group
    object: Literal['group.role']
    role: Role
