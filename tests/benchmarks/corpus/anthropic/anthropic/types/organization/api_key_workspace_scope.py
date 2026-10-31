
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class APIKeyWorkspaceScope(BaseModel):
    type: Literal['workspace']
    workspace_id: str
