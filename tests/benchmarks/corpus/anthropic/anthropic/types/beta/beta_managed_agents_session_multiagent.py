
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Annotated, TypeAlias
from ..._models import UnionDiscriminator
from .beta_managed_agents_session_multiagent20261001 import BetaManagedAgentsSessionMultiagent20261001
from .beta_managed_agents_session_multiagent_coordinator import BetaManagedAgentsSessionMultiagentCoordinator
BetaManagedAgentsSessionMultiagent: TypeAlias = Annotated[Union[BetaManagedAgentsSessionMultiagentCoordinator, BetaManagedAgentsSessionMultiagent20261001], UnionDiscriminator('type')]
