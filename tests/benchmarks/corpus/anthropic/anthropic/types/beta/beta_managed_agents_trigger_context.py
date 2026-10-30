
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Annotated, TypeAlias
from ..._models import UnionDiscriminator
from .beta_managed_agents_manual_trigger_context import BetaManagedAgentsManualTriggerContext
from .beta_managed_agents_schedule_trigger_context import BetaManagedAgentsScheduleTriggerContext
BetaManagedAgentsTriggerContext: TypeAlias = Annotated[Union[BetaManagedAgentsScheduleTriggerContext, BetaManagedAgentsManualTriggerContext], UnionDiscriminator('type')]
