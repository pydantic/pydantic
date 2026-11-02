
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from datetime import datetime
from typing_extensions import Literal
from ....._models import BaseModel

class BetaFederationRuleWorkspace(BaseModel):
    created_at: datetime
    created_by_actor_id: Optional[str] = None
    federation_rule_id: str
    type: Literal['federation_rule_workspace']
    workspace_id: str
    workspace_name: Optional[str] = None
