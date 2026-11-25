
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from datetime import datetime
from typing_extensions import Literal
from ..._models import BaseModel

class ServiceAccount(BaseModel):
    """Named non-human identity within the caller's organization.

    A service account is a pure identity: name + org. Authorization lives on
    whatever references it (federation rules).
    """
    id: str
    archived_at: Optional[datetime] = None
    archived_by_actor_id: Optional[str] = None
    created_at: datetime
    created_by_actor_id: Optional[str] = None
    description: Optional[str] = None
    name: str
    organization_role: Literal['admin', 'developer']
    type: Literal['service_account']
    updated_at: datetime
    updated_by_actor_id: Optional[str] = None
