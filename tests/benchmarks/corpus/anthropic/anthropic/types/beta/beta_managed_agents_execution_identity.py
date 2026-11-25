
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Annotated, TypeAlias
from ..._models import UnionDiscriminator
from .beta_managed_agents_aws_role_execution_identity import BetaManagedAgentsAWSRoleExecutionIdentity
from .beta_managed_agents_service_account_execution_identity import BetaManagedAgentsServiceAccountExecutionIdentity
BetaManagedAgentsExecutionIdentity: TypeAlias = Annotated[Union[BetaManagedAgentsAWSRoleExecutionIdentity, BetaManagedAgentsServiceAccountExecutionIdentity], UnionDiscriminator('type')]
