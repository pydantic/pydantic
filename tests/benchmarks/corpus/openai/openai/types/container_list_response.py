# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Optional
from typing_extensions import Literal
from .._models import BaseModel

class ExpiresAfter(BaseModel):
    """
    The container will expire after this time period.
    The anchor is the reference point for the expiration.
    The minutes is the number of minutes after the anchor before the container expires.
    """
    anchor: Optional[Literal['last_active_at']] = None
    minutes: Optional[int] = None

class NetworkPolicy(BaseModel):
    """Network access policy for the container."""
    type: Literal['allowlist', 'disabled']
    allowed_domains: Optional[List[str]] = None

class ContainerListResponse(BaseModel):
    id: str
    created_at: int
    name: str
    object: str
    status: str
    expires_after: Optional[ExpiresAfter] = None
    last_active_at: Optional[int] = None
    memory_limit: Optional[Literal['1g', '4g', '16g', '64g']] = None
    network_policy: Optional[NetworkPolicy] = None
