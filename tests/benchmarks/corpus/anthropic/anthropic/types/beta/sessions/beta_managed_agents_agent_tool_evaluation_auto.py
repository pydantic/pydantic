
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...._models import BaseModel
from .beta_managed_agents_agent_auto_evaluated_permission import BetaManagedAgentsAgentAutoEvaluatedPermission

class BetaManagedAgentsAgentToolEvaluationAuto(BaseModel):
    """
    The resolved permission_policy was auto: the server judged this invocation individually.
    """
    evaluated_permission: BetaManagedAgentsAgentAutoEvaluatedPermission
    type: Literal['auto']
