
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from datetime import datetime
from typing_extensions import Literal
from ...._models import BaseModel

class BetaTunnelCertificate(BaseModel):
    """A CA certificate attached to a tunnel."""
    id: str
    archived_at: Optional[datetime] = None
    created_at: datetime
    expires_at: Optional[datetime] = None
    fingerprint: str
    tunnel_id: str
    type: Literal['tunnel_certificate']
