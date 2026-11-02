
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Annotated, TypeAlias
from ..._models import UnionDiscriminator
from .beta_managed_agents_multiagent_inline_agents_enabled import BetaManagedAgentsMultiagentInlineAgentsEnabled
from .beta_managed_agents_multiagent_inline_agents_disabled import BetaManagedAgentsMultiagentInlineAgentsDisabled
BetaManagedAgentsMultiagentInlineAgents: TypeAlias = Annotated[Union[BetaManagedAgentsMultiagentInlineAgentsEnabled, BetaManagedAgentsMultiagentInlineAgentsDisabled], UnionDiscriminator('type')]
