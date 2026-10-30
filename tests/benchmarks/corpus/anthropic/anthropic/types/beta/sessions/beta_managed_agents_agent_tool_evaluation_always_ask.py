
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...._models import BaseModel

class BetaManagedAgentsAgentToolEvaluationAlwaysAsk(BaseModel):
    """
    The resolved permission_policy was always_ask; accompanies evaluated_permission "ask".
    """
    type: Literal['always_ask']
