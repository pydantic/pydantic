
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Dict, Optional
from datetime import datetime
from typing_extensions import Literal
from ..._models import BaseModel
from .data_residency import DataResidency

class Workspace(BaseModel):
    id: str
    archived_at: Optional[datetime] = None
    compartment_id: str
    created_at: datetime
    data_residency: DataResidency
    display_color: str
    external_key_id: Optional[str] = None
    name: str
    tags: Dict[str, str]
    type: Literal['workspace']
