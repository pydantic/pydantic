# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Dict, List, Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias
from ..._utils import PropertyInfo
from ..._models import BaseModel
from .beta_custom_tool import BetaCustomTool
from .beta_computer_tool import BetaComputerTool
from .beta_function_tool import BetaFunctionTool
from .beta_web_search_tool import BetaWebSearchTool
from .beta_apply_patch_tool import BetaApplyPatchTool
from .beta_file_search_tool import BetaFileSearchTool
from .beta_tool_search_tool import BetaToolSearchTool
from .beta_function_shell_tool import BetaFunctionShellTool
from .beta_web_search_preview_tool import BetaWebSearchPreviewTool
from .beta_computer_use_preview_tool import BetaComputerUsePreviewTool
from .beta_container_network_policy_disabled import BetaContainerNetworkPolicyDisabled
from .beta_tool_search_output_namespace_tool import BetaToolSearchOutputNamespaceTool
from .beta_container_network_policy_allowlist import BetaContainerNetworkPolicyAllowlist

class ToolMcpAllowedToolsMcpToolFilter(BaseModel):
    """A filter object to specify which tools are allowed."""
    read_only: Optional[bool] = None
    tool_names: Optional[List[str]] = None
ToolMcpAllowedTools: TypeAlias = Union[List[str], ToolMcpAllowedToolsMcpToolFilter, None]

class ToolMcpRequireApprovalMcpToolApprovalFilterAlways(BaseModel):
    """A filter object to specify which tools are allowed."""
    read_only: Optional[bool] = None
    tool_names: Optional[List[str]] = None

class ToolMcpRequireApprovalMcpToolApprovalFilterNever(BaseModel):
    """A filter object to specify which tools are allowed."""
    read_only: Optional[bool] = None
    tool_names: Optional[List[str]] = None

class ToolMcpRequireApprovalMcpToolApprovalFilter(BaseModel):
    """Specify which of the MCP server's tools require approval.

    Can be
    `always`, `never`, or a filter object associated with tools
    that require approval.
    """
    always: Optional[ToolMcpRequireApprovalMcpToolApprovalFilterAlways] = None
    never: Optional[ToolMcpRequireApprovalMcpToolApprovalFilterNever] = None
ToolMcpRequireApproval: TypeAlias = Union[ToolMcpRequireApprovalMcpToolApprovalFilter, Literal['always', 'never'], None]

class ToolMcp(BaseModel):
    """
    Give the model access to additional tools via remote Model Context Protocol
    (MCP) servers. [Learn more about MCP](https://developers.openai.com/api/docs/guides/tools-connectors-mcp).
    """
    server_label: str
    type: Literal['mcp']
    allowed_callers: Optional[List[Literal['direct', 'programmatic']]] = None
    allowed_tools: Optional[ToolMcpAllowedTools] = None
    authorization: Optional[str] = None
    connector_id: Optional[Literal['connector_dropbox', 'connector_gmail', 'connector_googlecalendar', 'connector_googledrive', 'connector_microsoftteams', 'connector_outlookcalendar', 'connector_outlookemail', 'connector_sharepoint']] = None
    defer_loading: Optional[bool] = None
    headers: Optional[Dict[str, str]] = None
    require_approval: Optional[ToolMcpRequireApproval] = None
    server_description: Optional[str] = None
    server_url: Optional[str] = None
    tunnel_id: Optional[str] = None
ToolCodeInterpreterContainerCodeInterpreterToolAutoNetworkPolicy: TypeAlias = Annotated[Union[BetaContainerNetworkPolicyDisabled, BetaContainerNetworkPolicyAllowlist], PropertyInfo(discriminator='type')]

class ToolCodeInterpreterContainerCodeInterpreterToolAuto(BaseModel):
    """Configuration for a code interpreter container.

    Optionally specify the IDs of the files to run the code on.
    """
    type: Literal['auto']
    file_ids: Optional[List[str]] = None
    memory_limit: Optional[Literal['1g', '4g', '16g', '64g']] = None
    network_policy: Optional[ToolCodeInterpreterContainerCodeInterpreterToolAutoNetworkPolicy] = None
ToolCodeInterpreterContainer: TypeAlias = Union[str, ToolCodeInterpreterContainerCodeInterpreterToolAuto]

class ToolCodeInterpreter(BaseModel):
    """A tool that runs Python code to help generate a response to a prompt."""
    container: ToolCodeInterpreterContainer
    type: Literal['code_interpreter']
    allowed_callers: Optional[List[Literal['direct', 'programmatic']]] = None

class ToolProgrammaticToolCalling(BaseModel):
    type: Literal['programmatic_tool_calling']

class ToolImageGenerationInputImageMask(BaseModel):
    """Optional mask for inpainting.

    Contains `image_url`
    (string, optional) and `file_id` (string, optional).
    """
    file_id: Optional[str] = None
    image_url: Optional[str] = None

class ToolImageGeneration(BaseModel):
    """A tool that generates images using the GPT image models."""
    type: Literal['image_generation']
    action: Optional[Literal['generate', 'edit', 'auto']] = None
    background: Optional[Literal['transparent', 'opaque', 'auto']] = None
    input_fidelity: Optional[Literal['high', 'low']] = None
    input_image_mask: Optional[ToolImageGenerationInputImageMask] = None
    model: Union[str, Literal['gpt-image-1', 'gpt-image-1-mini', 'gpt-image-2', 'gpt-image-2-2026-04-21', 'gpt-image-2.5-sunburst', 'gpt-image-2.5-sunburst-2026-09-08', 'gpt-image-2.5-flare', 'gpt-image-2.5-flare-2026-09-08', 'gpt-image-1.5', 'chatgpt-image-latest'], None] = None
    moderation: Optional[Literal['auto', 'low']] = None
    output_compression: Optional[int] = None
    output_format: Optional[Literal['png', 'webp', 'jpeg']] = None
    partial_images: Optional[int] = None
    quality: Optional[Literal['low', 'medium', 'high', 'xhigh', 'max', 'auto']] = None
    size: Union[str, Literal['1024x1024', '1024x1536', '1536x1024', 'auto'], None] = None

class ToolLocalShell(BaseModel):
    """A tool that allows the model to execute shell commands in a local environment."""
    type: Literal['local_shell']
Tool: TypeAlias = Annotated[Union[BetaFunctionTool, BetaFileSearchTool, BetaComputerTool, BetaComputerUsePreviewTool, BetaWebSearchTool, ToolMcp, ToolCodeInterpreter, ToolProgrammaticToolCalling, ToolImageGeneration, ToolLocalShell, BetaFunctionShellTool, BetaCustomTool, BetaToolSearchOutputNamespaceTool, BetaToolSearchTool, BetaWebSearchPreviewTool, BetaApplyPatchTool], PropertyInfo(discriminator='type')]

class Agent(BaseModel):
    """The agent that produced this item."""
    agent_name: str

class BetaResponseToolSearchOutputItemParam(BaseModel):
    tools: List[Tool]
    type: Literal['tool_search_output']
    id: Optional[str] = None
    agent: Optional[Agent] = None
    call_id: Optional[str] = None
    execution: Optional[Literal['server', 'client']] = None
    status: Optional[Literal['in_progress', 'completed', 'incomplete']] = None
