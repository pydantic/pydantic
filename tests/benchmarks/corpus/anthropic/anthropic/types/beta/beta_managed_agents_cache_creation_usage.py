
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from ..._models import BaseModel

class BetaManagedAgentsCacheCreationUsage(BaseModel):
    """Prompt-cache creation token usage broken down by cache lifetime."""
    ephemeral_1h_input_tokens: Optional[int] = None
    ephemeral_5m_input_tokens: Optional[int] = None
