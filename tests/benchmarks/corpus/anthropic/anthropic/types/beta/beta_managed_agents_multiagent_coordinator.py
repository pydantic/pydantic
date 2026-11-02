
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import List, Union
from typing_extensions import Literal, Annotated, TypeAlias
from ..._models import BaseModel, UnionDiscriminator
from .beta_managed_agents_advisor import BetaManagedAgentsAdvisor
from .beta_managed_agents_agent_reference import BetaManagedAgentsAgentReference
Agent: TypeAlias = Annotated[Union[BetaManagedAgentsAgentReference, BetaManagedAgentsAdvisor], UnionDiscriminator('type')]

class BetaManagedAgentsMultiagentCoordinator(BaseModel):
    """Resolved coordinator topology with a concrete agent roster."""
    agents: List[Agent]
    type: Literal['coordinator']
