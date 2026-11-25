
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel
from .beta_managed_agents_multiagent_advisor import BetaManagedAgentsMultiagentAdvisor
from .beta_managed_agents_session_multiagent_subagents import BetaManagedAgentsSessionMultiagentSubagents
from .beta_managed_agents_session_multiagent_workflows import BetaManagedAgentsSessionMultiagentWorkflows

class BetaManagedAgentsSessionMultiagent20261001(BaseModel):
    """
    Resolved multiagent configuration with three members, as copied to the `session` at creation.
    """
    advisor: BetaManagedAgentsMultiagentAdvisor
    subagents: BetaManagedAgentsSessionMultiagentSubagents
    type: Literal['multiagent_20261001']
    workflows: BetaManagedAgentsSessionMultiagentWorkflows
