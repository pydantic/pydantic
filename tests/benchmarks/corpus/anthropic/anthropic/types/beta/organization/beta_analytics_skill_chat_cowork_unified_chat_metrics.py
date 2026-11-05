
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from ...._models import BaseModel

class BetaAnalyticsSkillChatCoworkUnifiedChatMetrics(BaseModel):
    """
    A skill's use in chat conversations recorded while members had
    Chat and Cowork unified turned on.
    """
    distinct_conversation_skill_used_count: Optional[int] = None
