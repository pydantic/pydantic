
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from datetime import datetime
from typing_extensions import Literal
from ...._models import BaseModel
from ..beta_organization_role import BetaOrganizationRole

class BetaOrganizationUser(BaseModel):
    id: str
    added_at: datetime
    email: str
    name: str
    role: BetaOrganizationRole
    type: Literal['user']
