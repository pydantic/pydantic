
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from ...._models import BaseModel

class BetaManagedAgentsRefreshHTTPResponse(BaseModel):
    """An HTTP response captured during a credential validation probe."""
    body: str
    body_truncated: bool
    content_type: str
    status_code: int
