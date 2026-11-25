
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import List, Optional
from datetime import datetime
from typing_extensions import Literal
from ...._models import BaseModel
from ..beta_organization_role import BetaOrganizationRole

class BetaOrganizationInvite(BaseModel):
    id: str
    accepted_at: Optional[datetime] = None
    email: str
    expires_at: datetime
    invited_at: datetime
    rbac_group_ids: List[str]
    role: BetaOrganizationRole
    status: Literal['accepted', 'deleted', 'expired', 'pending']
    type: Literal['invite']
