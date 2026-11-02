
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import List, Optional
from datetime import datetime
from typing_extensions import Literal
from ...._models import BaseModel

class BetaRBACGroup(BaseModel):
    id: str
    created_at: datetime
    name: str
    role_ids: Optional[List[str]] = None
    source_type: Literal['direct', 'scim']
    type: Literal['rbac_group']
    updated_at: datetime
