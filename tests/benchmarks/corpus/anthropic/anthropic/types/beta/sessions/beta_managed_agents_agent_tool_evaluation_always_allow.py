
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...._models import BaseModel

class BetaManagedAgentsAgentToolEvaluationAlwaysAllow(BaseModel):
    """
    The resolved permission_policy was always_allow; accompanies evaluated_permission "allow".
    """
    type: Literal['always_allow']
