
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from datetime import datetime
from ...._models import BaseModel

class FederationIssuerPollStatus(BaseModel):
    """Status of automatic JWKS polling for a federation issuer.

    Anthropic periodically fetches the issuer's signing keys in the
    background. These fields summarize the most recent fetches so the
    health of the JWKS endpoint can be monitored.
    """
    consecutive_failures: int
    last_fetched_at: Optional[datetime] = None
    next_poll_at: Optional[datetime] = None
