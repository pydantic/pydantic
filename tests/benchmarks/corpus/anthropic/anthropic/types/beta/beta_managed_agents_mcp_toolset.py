
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import List
from typing_extensions import Literal
from ..._models import BaseModel
from .beta_managed_agents_mcp_tool_config import BetaManagedAgentsMCPToolConfig
from .beta_managed_agents_mcp_toolset_default_config import BetaManagedAgentsMCPToolsetDefaultConfig

class BetaManagedAgentsMCPToolset(BaseModel):
    configs: List[BetaManagedAgentsMCPToolConfig]
    default_config: BetaManagedAgentsMCPToolsetDefaultConfig
    mcp_server_name: str
    type: Literal['mcp_toolset']
