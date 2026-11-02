
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel
from .sessions.beta_managed_agents_text_block import BetaManagedAgentsTextBlock

class BetaManagedAgentsDeltaContent(BaseModel):
    content: BetaManagedAgentsTextBlock
    type: Literal['content_delta']
    index: Optional[int] = None
