
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import List
from typing_extensions import Literal
from ..._models import BaseModel
from .beta_managed_agents_agent_reference import BetaManagedAgentsAgentReference
from .beta_managed_agents_multiagent_inline_agents import BetaManagedAgentsMultiagentInlineAgents

class BetaManagedAgentsMultiagentWorkflowsEnabled(BaseModel):
    """The agent can start workflow runs."""
    inline_agents: BetaManagedAgentsMultiagentInlineAgents
    predefined_agents: List[BetaManagedAgentsAgentReference]
    type: Literal['enabled']
