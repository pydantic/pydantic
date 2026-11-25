
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import List, Optional
from datetime import datetime
from typing_extensions import Literal
from ..._models import BaseModel
from ..organization_role import OrganizationRole

class OrganizationInvite(BaseModel):
    id: str
    accepted_at: Optional[datetime] = None
    email: str
    expires_at: datetime
    invited_at: datetime
    rbac_group_ids: List[str]
    role: OrganizationRole
    status: Literal['accepted', 'deleted', 'expired', 'pending']
    type: Literal['invite']
