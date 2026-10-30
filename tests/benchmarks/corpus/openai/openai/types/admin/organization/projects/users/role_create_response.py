# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...role import Role
from ......_models import BaseModel
from ...organization_user import OrganizationUser

class RoleCreateResponse(BaseModel):
    """Role assignment linking a user to a role."""
    object: Literal['user.role']
    role: Role
    user: OrganizationUser
