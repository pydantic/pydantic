
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...._models import BaseModel

class BetaManagedAgentsAgentAutoEvaluatedPermissionDeny(BaseModel):
    """
    The server judged the invocation high-risk; it does not execute and a synthetic error tool result is appended.
    """
    reason_code: str
    type: Literal['deny']
