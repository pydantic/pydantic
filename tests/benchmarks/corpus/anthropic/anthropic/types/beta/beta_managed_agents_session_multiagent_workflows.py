
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Annotated, TypeAlias
from ..._models import UnionDiscriminator
from .beta_managed_agents_multiagent_workflows_disabled import BetaManagedAgentsMultiagentWorkflowsDisabled
from .beta_managed_agents_session_multiagent_workflows_enabled import BetaManagedAgentsSessionMultiagentWorkflowsEnabled
BetaManagedAgentsSessionMultiagentWorkflows: TypeAlias = Annotated[Union[BetaManagedAgentsSessionMultiagentWorkflowsEnabled, BetaManagedAgentsMultiagentWorkflowsDisabled], UnionDiscriminator('type')]
