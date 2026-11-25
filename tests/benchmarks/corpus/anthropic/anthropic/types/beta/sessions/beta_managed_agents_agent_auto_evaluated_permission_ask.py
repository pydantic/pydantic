
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...._models import BaseModel

class BetaManagedAgentsAgentAutoEvaluatedPermissionAsk(BaseModel):
    """The server reached no judgement; the invocation is held for client approval."""
    reason_code: str
    type: Literal['ask']
