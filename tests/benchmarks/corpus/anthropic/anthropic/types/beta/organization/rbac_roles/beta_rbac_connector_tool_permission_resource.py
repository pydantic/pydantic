
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ....._models import BaseModel

class BetaRBACConnectorToolPermissionResource(BaseModel):
    connector_id: str
    tool_name: str
    type: Literal['connector_tool']
