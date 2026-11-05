
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ....._models import BaseModel

class WorkspaceRemoveResponse(BaseModel):
    federation_rule_id: str
    type: Literal['federation_rule_workspace_deleted']
    workspace_id: str
