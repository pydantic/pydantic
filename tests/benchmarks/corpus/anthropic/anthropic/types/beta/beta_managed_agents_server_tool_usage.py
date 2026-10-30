
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from ..._models import BaseModel

class BetaManagedAgentsServerToolUsage(BaseModel):
    """Cumulative count of server-executed tool invocations, broken down by tool."""
    web_fetch_requests: Optional[int] = None
    web_search_requests: Optional[int] = None
