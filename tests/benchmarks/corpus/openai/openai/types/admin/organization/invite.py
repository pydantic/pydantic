# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Optional
from typing_extensions import Literal
from ...._models import BaseModel

class Project(BaseModel):
    id: str
    role: Literal['member', 'owner']

class Invite(BaseModel):
    """Represents an individual `invite` to the organization."""
    id: str
    created_at: int
    email: str
    object: Literal['organization.invite']
    projects: List[Project]
    role: Literal['owner', 'reader']
    status: Literal['accepted', 'expired', 'pending']
    accepted_at: Optional[int] = None
    expires_at: Optional[int] = None
