
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import List, Union
from typing_extensions import Literal, Annotated, TypeAlias
from ..._models import BaseModel, UnionDiscriminator
from .beta_managed_agents_advisor import BetaManagedAgentsAdvisor
from .beta_managed_agents_session_thread_agent import BetaManagedAgentsSessionThreadAgent
Agent: TypeAlias = Annotated[Union[BetaManagedAgentsSessionThreadAgent, BetaManagedAgentsAdvisor], UnionDiscriminator('type')]

class BetaManagedAgentsSessionMultiagentCoordinator(BaseModel):
    """
    Resolved coordinator topology with full agent definitions for each roster member.
    """
    agents: List[Agent]
    type: Literal['coordinator']
