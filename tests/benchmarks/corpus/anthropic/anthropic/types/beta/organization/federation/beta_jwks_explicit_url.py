
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ....._models import BaseModel

class BetaJWKSExplicitURL(BaseModel):
    """JWKS fetched from a fixed endpoint."""
    type: Literal['explicit_url']
    url: str
    ca_cert_pem: Optional[str] = None
