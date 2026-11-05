
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Annotated, TypeAlias
from ..._models import UnionDiscriminator
from .beta_managed_agents_multiagent_subagents_disabled import BetaManagedAgentsMultiagentSubagentsDisabled
from .beta_managed_agents_session_multiagent_subagents_enabled import BetaManagedAgentsSessionMultiagentSubagentsEnabled
BetaManagedAgentsSessionMultiagentSubagents: TypeAlias = Annotated[Union[BetaManagedAgentsSessionMultiagentSubagentsEnabled, BetaManagedAgentsMultiagentSubagentsDisabled], UnionDiscriminator('type')]
