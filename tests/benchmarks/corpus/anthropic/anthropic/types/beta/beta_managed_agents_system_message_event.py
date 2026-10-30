
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import List, Optional
from datetime import datetime
from typing_extensions import Literal
from ..._models import BaseModel
from .beta_managed_agents_system_content_block import BetaManagedAgentsSystemContentBlock

class BetaManagedAgentsSystemMessageEvent(BaseModel):
    """A mid-conversation system message event.

    Carries system-role content that is appended to the session as a `role: "system"` turn.
    """
    id: str
    content: List[BetaManagedAgentsSystemContentBlock]
    type: Literal['system.message']
    processed_at: Optional[datetime] = None
