
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ...._models import BaseModel
from .beta_workspace_role import BetaWorkspaceRole

class BetaServiceAccountWorkspaceMember(BaseModel):
    created_by_actor_id: Optional[str] = None
    implicit: Optional[bool] = None
    service_account_id: str
    type: Literal['service_account_workspace_member']
    workspace_id: str
    workspace_role: BetaWorkspaceRole
