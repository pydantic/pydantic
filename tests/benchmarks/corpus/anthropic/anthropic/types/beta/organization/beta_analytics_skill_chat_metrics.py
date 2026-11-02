
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from ...._models import BaseModel

class BetaAnalyticsSkillChatMetrics(BaseModel):
    """Claude.ai activity metrics for a single skill on a given day."""
    distinct_conversation_skill_used_count: Optional[int] = None
