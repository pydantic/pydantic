# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ....._models import BaseModel

class UserRetrieveResponse(BaseModel):
    """Details about a user returned from an organization group membership lookup."""
    id: str
    email: Optional[str] = None
    is_service_account: Optional[bool] = None
    name: str
    picture: Optional[str] = None
    user_type: Literal['user', 'tenant_user']
