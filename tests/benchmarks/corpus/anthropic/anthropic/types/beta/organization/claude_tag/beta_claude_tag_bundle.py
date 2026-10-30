
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from datetime import datetime
from typing_extensions import Literal
from ....._models import BaseModel

class BetaClaudeTagBundle(BaseModel):
    """
    A named set of access that Claude can use in a Slack channel or a Slack workspace: connectors, repositories and credentials. Created and edited in claude.ai.
    """
    id: str
    created_at: datetime
    description: Optional[str] = None
    display_name: str
    type: Literal['bundle']
    updated_at: datetime
