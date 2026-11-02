
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from ...._models import BaseModel

class BetaAnalyticsLinesOfCode(BaseModel):
    """Lines of code added and removed via Claude Code."""
    added_count: int
    removed_count: int
