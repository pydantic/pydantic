
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class BetaManagedAgentsAWSRoleExecutionIdentity(BaseModel):
    """An AWS IAM role principal as returned in API responses."""
    role_arn: str
    type: Literal['aws_role']
