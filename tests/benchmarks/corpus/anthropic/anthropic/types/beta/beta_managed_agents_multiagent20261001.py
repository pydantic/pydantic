
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel
from .beta_managed_agents_multiagent_advisor import BetaManagedAgentsMultiagentAdvisor
from .beta_managed_agents_multiagent_subagents import BetaManagedAgentsMultiagentSubagents
from .beta_managed_agents_multiagent_workflows import BetaManagedAgentsMultiagentWorkflows

class BetaManagedAgentsMultiagent20261001(BaseModel):
    """
    Resolved multiagent configuration with three members, each enabled or disabled on its own.
    """
    advisor: BetaManagedAgentsMultiagentAdvisor
    subagents: BetaManagedAgentsMultiagentSubagents
    type: Literal['multiagent_20261001']
    workflows: BetaManagedAgentsMultiagentWorkflows
