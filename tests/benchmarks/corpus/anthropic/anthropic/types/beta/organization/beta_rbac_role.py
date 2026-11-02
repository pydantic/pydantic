
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from datetime import datetime
from typing_extensions import Literal
from ...._models import BaseModel

class BetaRBACRole(BaseModel):
    id: str
    created_at: datetime
    display_name: str
    type: Literal['rbac_role']
    updated_at: datetime
