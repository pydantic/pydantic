
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from datetime import datetime
from typing_extensions import Literal
from ....._models import BaseModel

class BetaRBACGroupMember(BaseModel):
    created_at: datetime
    email: str
    rbac_group_id: str
    type: Literal['rbac_group_member']
    user_id: str
