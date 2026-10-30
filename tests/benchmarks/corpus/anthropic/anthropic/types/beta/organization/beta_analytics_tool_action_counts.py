
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from ...._models import BaseModel

class BetaAnalyticsToolActionCounts(BaseModel):
    """Accepted/rejected counts for a single Claude Code tool type."""
    accepted_count: int
    rejected_count: int
