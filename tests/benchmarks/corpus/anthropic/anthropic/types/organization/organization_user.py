
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from datetime import datetime
from typing_extensions import Literal
from ..._models import BaseModel
from ..organization_role import OrganizationRole

class OrganizationUser(BaseModel):
    id: str
    added_at: datetime
    email: str
    name: str
    role: OrganizationRole
    type: Literal['user']
