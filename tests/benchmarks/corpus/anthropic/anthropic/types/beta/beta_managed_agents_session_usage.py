
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from ..._models import BaseModel
from ..beta_monetary_amount import BetaMonetaryAmount
from .beta_managed_agents_server_tool_usage import BetaManagedAgentsServerToolUsage
from .beta_managed_agents_cache_creation_usage import BetaManagedAgentsCacheCreationUsage

class BetaManagedAgentsSessionUsage(BaseModel):
    """Cumulative token usage for a session across all turns."""
    active_seconds: Optional[float] = None
    cache_creation: Optional[BetaManagedAgentsCacheCreationUsage] = None
    cache_read_input_tokens: Optional[int] = None
    input_tokens: Optional[int] = None
    list_cost: Optional[BetaMonetaryAmount] = None
    output_tokens: Optional[int] = None
    server_tool_use: Optional[BetaManagedAgentsServerToolUsage] = None
