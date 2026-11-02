
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from ....._models import BaseModel
from ...beta_cache_creation import BetaCacheCreation
from ..beta_analytics_server_tool_use import BetaAnalyticsServerToolUse

class BetaAnalyticsUsageMetrics(BaseModel):
    """The token usage of one row."""
    cache_creation: BetaCacheCreation
    cache_read_input_tokens: int
    output_tokens: int
    requests: Optional[int] = None
    server_tool_use: BetaAnalyticsServerToolUse
    total_tokens: int
    uncached_input_tokens: int
