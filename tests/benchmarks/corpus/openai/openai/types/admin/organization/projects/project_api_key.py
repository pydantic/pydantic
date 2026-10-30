# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ....._models import BaseModel

class OwnerServiceAccount(BaseModel):
    """The service account that owns a project API key."""
    id: str
    created_at: int
    name: str
    role: str

class OwnerUser(BaseModel):
    """The user that owns a project API key."""
    id: str
    created_at: int
    email: str
    name: str
    role: str

class Owner(BaseModel):
    service_account: Optional[OwnerServiceAccount] = None
    type: Optional[Literal['user', 'service_account']] = None
    user: Optional[OwnerUser] = None

class ProjectAPIKey(BaseModel):
    """Represents an individual API key in a project."""
    id: str
    created_at: int
    last_used_at: Optional[int] = None
    name: str
    object: Literal['organization.project.api_key']
    owner: Owner
    owner_project_access: Literal['active', 'inactive']
    redacted_value: str
    expires_at: Optional[int] = None
