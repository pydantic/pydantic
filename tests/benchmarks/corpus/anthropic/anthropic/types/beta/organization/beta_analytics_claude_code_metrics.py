
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from ...._models import BaseModel
from .beta_analytics_tool_actions import BetaAnalyticsToolActions
from .beta_analytics_core_code_metrics import BetaAnalyticsCoreCodeMetrics

class BetaAnalyticsClaudeCodeMetrics(BaseModel):
    """Claude Code activity metrics for a single user on a given day."""
    core_metrics: BetaAnalyticsCoreCodeMetrics
    tool_actions: BetaAnalyticsToolActions
