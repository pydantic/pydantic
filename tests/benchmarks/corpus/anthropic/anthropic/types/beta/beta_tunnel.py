
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from datetime import datetime
from typing_extensions import Literal
from ..._models import BaseModel

class BetaTunnel(BaseModel):
    """An MCP tunnel."""
    id: str
    archived_at: Optional[datetime] = None
    created_at: datetime
    display_name: Optional[str] = None
    domain: str
    type: Literal['tunnel']
