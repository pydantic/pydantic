
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ....._models import BaseModel

class BetaJWKSDiscovery(BaseModel):
    """JWKS via the issuer's OIDC discovery document."""
    type: Literal['discovery']
    ca_cert_pem: Optional[str] = None
    discovery_base: Optional[str] = None
