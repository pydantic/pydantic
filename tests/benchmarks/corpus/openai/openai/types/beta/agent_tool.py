# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Dict, List, Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias
from ..._utils import PropertyInfo
from ..._models import BaseModel
from .mcp_transport import McpTransport

class AgentToolResourceFunction(BaseModel):
    """A function defined by the application."""
    defer_loading: bool
    description: str
    name: str
    parameters: Dict[str, object]
    type: Literal['function']

class AgentToolResourceProgrammaticToolCalling(BaseModel):
    """Enables calling tools from model-generated code."""
    enabled: bool
    type: Literal['programmatic_tool_calling']

class AgentToolResourceMcp(BaseModel):
    """Tools provided by a remote MCP server."""
    allowed_tools: Optional[List[str]] = None
    connection_origin: Literal['service', 'environment']
    credential_id: Optional[str] = None
    request_metadata: Dict[str, object]
    required: bool
    server_label: str
    transport: McpTransport
    type: Literal['mcp']

class AgentToolResourceWebSearchLocation(BaseModel):
    """Approximate location used to localize search results, if provided."""
    city: Optional[str] = None
    country: Optional[str] = None
    region: Optional[str] = None
    timezone: Optional[str] = None

class AgentToolResourceWebSearch(BaseModel):
    """Web search."""
    allowed_domains: Optional[List[str]] = None
    context_size: Literal['low', 'medium', 'high']
    location: Optional[AgentToolResourceWebSearchLocation] = None
    mode: Literal['disabled', 'cached', 'live']
    type: Literal['web_search']

class AgentToolResourceComputerUse(BaseModel):
    """Browser use in an OpenAI-hosted session."""
    include_screenshots: bool
    type: Literal['computer_use']

class AgentToolResourceAutomations(BaseModel):
    """Lets the agent manage its own scheduled wakeups."""
    type: Literal['automations']
AgentTool: TypeAlias = Annotated[Union[AgentToolResourceFunction, AgentToolResourceProgrammaticToolCalling, AgentToolResourceMcp, AgentToolResourceWebSearch, AgentToolResourceComputerUse, AgentToolResourceAutomations], PropertyInfo(discriminator='type')]
