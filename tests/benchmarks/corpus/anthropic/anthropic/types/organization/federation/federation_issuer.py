
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Union, Optional
from datetime import datetime
from typing_extensions import Literal, Annotated, TypeAlias
from ...._models import BaseModel, UnionDiscriminator
from .jwks_inline import JWKSInline
from .jwks_discovery import JWKSDiscovery
from .jwks_explicit_url import JWKSExplicitURL
from .federation_issuer_poll_status import FederationIssuerPollStatus
JWKS: TypeAlias = Annotated[Union[JWKSDiscovery, JWKSExplicitURL, JWKSInline], UnionDiscriminator('type')]

class FederationIssuer(BaseModel):
    """Registered external OIDC identity provider.

    Records an external IdP the organization trusts for the RFC 7523
    jwt-bearer grant. The `issuer_url` must match the JWT `iss` claim exactly.
    """
    id: str
    archived_at: Optional[datetime] = None
    archived_by_actor_id: Optional[str] = None
    check_jti: bool
    created_at: datetime
    created_by_actor_id: Optional[str] = None
    issuer_url: str
    jwks: JWKS
    jwks_polling_disabled_at: Optional[datetime] = None
    max_jwt_lifetime_seconds: int
    name: str
    poll_status: Optional[FederationIssuerPollStatus] = None
    type: Literal['federation_issuer']
    updated_at: datetime
    updated_by_actor_id: Optional[str] = None
