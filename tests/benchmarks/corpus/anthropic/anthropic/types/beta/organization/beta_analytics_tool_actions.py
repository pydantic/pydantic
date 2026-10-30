
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from ...._models import BaseModel
from .beta_analytics_tool_action_counts import BetaAnalyticsToolActionCounts

class BetaAnalyticsToolActions(BaseModel):
    """Per-tool accepted/rejected counts for Claude Code file modification tools."""
    edit_tool: BetaAnalyticsToolActionCounts
    multi_edit_tool: BetaAnalyticsToolActionCounts
    notebook_edit_tool: BetaAnalyticsToolActionCounts
    write_tool: BetaAnalyticsToolActionCounts
