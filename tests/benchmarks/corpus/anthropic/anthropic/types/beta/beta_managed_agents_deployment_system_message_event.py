
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import List
from typing_extensions import Literal
from ..._models import BaseModel
from .beta_managed_agents_system_content_block import BetaManagedAgentsSystemContentBlock

class BetaManagedAgentsDeploymentSystemMessageEvent(BaseModel):
    """
    Privileged context for the accompanying turn and all subsequent turns, appended to the session's system context as a `role: "system"` turn rather than replacing the top-level system prompt.
    """
    content: List[BetaManagedAgentsSystemContentBlock]
    type: Literal['system.message']
