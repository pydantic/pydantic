
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...._models import BaseModel
from .beta_workspace_role import BetaWorkspaceRole

class BetaWorkspaceMember(BaseModel):
    type: Literal['workspace_member']
    user_id: str
    workspace_id: str
    workspace_role: BetaWorkspaceRole
