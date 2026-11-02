
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from ...._models import BaseModel

class BetaAnalyticsConnectorChatCoworkUnifiedChatMetrics(BaseModel):
    """
    A connector's use in chat conversations recorded while members had
    Chat and Cowork unified turned on.
    """
    distinct_conversation_connector_used_count: Optional[int] = None
