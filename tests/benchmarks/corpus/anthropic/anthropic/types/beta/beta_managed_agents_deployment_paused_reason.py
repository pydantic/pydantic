
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Annotated, TypeAlias
from ..._models import UnionDiscriminator
from .beta_managed_agents_error_deployment_paused_reason import BetaManagedAgentsErrorDeploymentPausedReason
from .beta_managed_agents_manual_deployment_paused_reason import BetaManagedAgentsManualDeploymentPausedReason
BetaManagedAgentsDeploymentPausedReason: TypeAlias = Annotated[Union[BetaManagedAgentsManualDeploymentPausedReason, BetaManagedAgentsErrorDeploymentPausedReason], UnionDiscriminator('type')]
