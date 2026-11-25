# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Optional
from typing_extensions import Literal
from ...._models import BaseModel

class ProjectsData(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    role: Optional[str] = None

class Projects(BaseModel):
    """Projects associated with the user, if included."""
    data: List[ProjectsData]
    object: Literal['list']

class User(BaseModel):
    """Nested user details."""
    id: str
    object: Literal['user']
    banned: Optional[bool] = None
    banned_at: Optional[int] = None
    email: Optional[str] = None
    enabled: Optional[bool] = None
    name: Optional[str] = None
    picture: Optional[str] = None

class OrganizationUser(BaseModel):
    """Represents an individual `user` within an organization."""
    id: str
    added_at: int
    object: Literal['organization.user']
    api_key_last_used_at: Optional[int] = None
    created: Optional[int] = None
    developer_persona: Optional[str] = None
    email: Optional[str] = None
    is_default: Optional[bool] = None
    is_scale_tier_authorized_purchaser: Optional[bool] = None
    is_scim_managed: Optional[bool] = None
    is_service_account: Optional[bool] = None
    name: Optional[str] = None
    projects: Optional[Projects] = None
    role: Optional[str] = None
    technical_level: Optional[str] = None
    user: Optional[User] = None
