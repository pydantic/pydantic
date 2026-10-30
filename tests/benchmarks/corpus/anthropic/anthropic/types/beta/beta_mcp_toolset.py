
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Dict, List, Optional
from typing_extensions import Literal
from ..._models import BaseModel
from .beta_mcp_tool_param import BetaMCPToolParam
from .beta_mcp_tool_config import BetaMCPToolConfig
from .beta_cache_control_ephemeral import BetaCacheControlEphemeral
from .beta_mcp_tool_default_config import BetaMCPToolDefaultConfig

class BetaMCPToolset(BaseModel):
    """Configuration for a group of tools from an MCP server.

    Allows configuring enabled status and defer_loading for all tools
    from an MCP server, with optional per-tool overrides.
    """
    mcp_server_name: str
    type: Literal['mcp_toolset']
    cache_control: Optional[BetaCacheControlEphemeral] = None
    configs: Optional[Dict[str, BetaMCPToolConfig]] = None
    default_config: Optional[BetaMCPToolDefaultConfig] = None
    tools: Optional[List[BetaMCPToolParam]] = None
