
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import List
from typing_extensions import Literal
from ..._models import BaseModel
from .beta_managed_agents_agent_tool_config import BetaManagedAgentsAgentToolConfig
from .beta_managed_agents_agent_toolset_default_config import BetaManagedAgentsAgentToolsetDefaultConfig

class BetaManagedAgentsAgentToolset20260401(BaseModel):
    configs: List[BetaManagedAgentsAgentToolConfig]
    default_config: BetaManagedAgentsAgentToolsetDefaultConfig
    type: Literal['agent_toolset_20260401']
