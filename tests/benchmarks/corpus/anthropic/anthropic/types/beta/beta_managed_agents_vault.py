
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Dict, Optional
from datetime import datetime
from typing_extensions import Literal
from ..._models import BaseModel

class BetaManagedAgentsVault(BaseModel):
    """A vault that stores credentials for use by agents during sessions."""
    id: str
    archived_at: Optional[datetime] = None
    created_at: datetime
    display_name: str
    metadata: Dict[str, str]
    type: Literal['vault']
    updated_at: datetime
