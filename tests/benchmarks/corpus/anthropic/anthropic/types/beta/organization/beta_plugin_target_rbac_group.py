
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...._models import BaseModel

class BetaPluginTargetRBACGroup(BaseModel):
    rbac_group_id: str
    type: Literal['rbac_group']
