
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Union, Optional
from datetime import datetime
from typing_extensions import Literal, Annotated, TypeAlias
from ....._models import BaseModel, UnionDiscriminator
from .beta_jwks_inline import BetaJWKSInline
from .beta_jwks_discovery import BetaJWKSDiscovery
from .beta_jwks_explicit_url import BetaJWKSExplicitURL
from .beta_federation_issuer_poll_status import BetaFederationIssuerPollStatus
JWKS: TypeAlias = Annotated[Union[BetaJWKSDiscovery, BetaJWKSExplicitURL, BetaJWKSInline], UnionDiscriminator('type')]

class BetaFederationIssuer(BaseModel):
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
    poll_status: Optional[BetaFederationIssuerPollStatus] = None
    type: Literal['federation_issuer']
    updated_at: datetime
    updated_by_actor_id: Optional[str] = None
