
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Annotated, TypeAlias
from ..._models import UnionDiscriminator
from .beta_managed_agents_multiagent_advisor_enabled import BetaManagedAgentsMultiagentAdvisorEnabled
from .beta_managed_agents_multiagent_advisor_disabled import BetaManagedAgentsMultiagentAdvisorDisabled
BetaManagedAgentsMultiagentAdvisor: TypeAlias = Annotated[Union[BetaManagedAgentsMultiagentAdvisorEnabled, BetaManagedAgentsMultiagentAdvisorDisabled], UnionDiscriminator('type')]
