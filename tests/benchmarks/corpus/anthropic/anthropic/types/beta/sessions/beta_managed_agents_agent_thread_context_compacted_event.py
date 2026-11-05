
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from datetime import datetime
from typing_extensions import Literal
from ...._models import BaseModel

class BetaManagedAgentsAgentThreadContextCompactedEvent(BaseModel):
    """Indicates that context compaction (summarization) occurred during the session."""
    id: str
    processed_at: datetime
    type: Literal['agent.thread_context_compacted']
