# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ......_models import BaseModel

class APIKeyCreateResponse(BaseModel):
    id: str
    created_at: int
    name: str
    object: Literal['organization.project.service_account.api_key']
    value: str
    expires_at: Optional[int] = None
