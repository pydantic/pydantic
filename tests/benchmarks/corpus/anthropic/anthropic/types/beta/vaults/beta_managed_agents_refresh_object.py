
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ...._models import BaseModel
from .beta_managed_agents_refresh_http_response import BetaManagedAgentsRefreshHTTPResponse

class BetaManagedAgentsRefreshObject(BaseModel):
    """Outcome of a refresh-token exchange attempted during credential validation."""
    http_response: Optional[BetaManagedAgentsRefreshHTTPResponse] = None
    status: Literal['succeeded', 'failed', 'connect_error', 'no_refresh_token']
