
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from ...._models import BaseModel

class BetaAnalyticsPluginClaudeCodeMetrics(BaseModel):
    """Claude Code activity metrics for a single plugin on a given day."""
    distinct_session_plugin_used_count: Optional[int] = None
