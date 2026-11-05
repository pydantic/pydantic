
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from ...._models import BaseModel

class BetaAnalyticsSkillCoworkMetrics(BaseModel):
    """Cowork activity metrics for a single skill on a given day."""
    distinct_session_skill_used_count: Optional[int] = None
