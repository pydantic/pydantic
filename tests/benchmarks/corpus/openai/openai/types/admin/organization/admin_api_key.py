# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ...._models import BaseModel

class Owner(BaseModel):
    id: Optional[str] = None
    created_at: Optional[int] = None
    name: Optional[str] = None
    object: Optional[str] = None
    role: Optional[str] = None
    type: Optional[str] = None

class AdminAPIKey(BaseModel):
    """Represents an individual Admin API key in an org."""
    id: str
    created_at: int
    expires_at: Optional[int] = None
    object: Literal['organization.admin_api_key']
    owner: Owner
    redacted_value: str
    last_used_at: Optional[int] = None
    name: Optional[str] = None
