# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Dict, List, Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias
from .tool import Tool
from ..._utils import PropertyInfo
from ..._models import BaseModel
from .mcp_tool_call_error import McpToolCallError
from .response_output_message import ResponseOutputMessage
from .response_reasoning_item import ResponseReasoningItem
from .response_compaction_item import ResponseCompactionItem
from .response_custom_tool_call import ResponseCustomToolCall
from .response_tool_search_call import ResponseToolSearchCall
from .response_computer_tool_call import ResponseComputerToolCall
from .response_function_tool_call import ResponseFunctionToolCall
from .response_function_web_search import ResponseFunctionWebSearch
from .response_apply_patch_tool_call import ResponseApplyPatchToolCall
from .response_file_search_tool_call import ResponseFileSearchToolCall
from .response_tool_search_output_item import ResponseToolSearchOutputItem
from .response_function_shell_tool_call import ResponseFunctionShellToolCall
from .response_code_interpreter_tool_call import ResponseCodeInterpreterToolCall
from .response_apply_patch_tool_call_output import ResponseApplyPatchToolCallOutput
from .response_custom_tool_call_output_item import ResponseCustomToolCallOutputItem
from .response_computer_tool_call_output_item import ResponseComputerToolCallOutputItem
from .response_function_tool_call_output_item import ResponseFunctionToolCallOutputItem
from .response_function_shell_tool_call_output import ResponseFunctionShellToolCallOutput

class Program(BaseModel):
    id: str
    call_id: str
    code: str
    fingerprint: str
    type: Literal['program']

class ProgramOutput(BaseModel):
    id: str
    call_id: str
    result: str
    status: Literal['completed', 'incomplete']
    type: Literal['program_output']

class AdditionalTools(BaseModel):
    id: str
    role: Literal['unknown', 'user', 'assistant', 'system', 'critic', 'discriminator', 'developer', 'tool']
    tools: List[Tool]
    type: Literal['additional_tools']

class ImageGenerationCallErrorModerationDetails(BaseModel):
    """Public details for a `moderation_blocked` error, when available."""
    categories: List[str]
    moderation_stage: Literal['input', 'output', 'unknown']

class ImageGenerationCallError(BaseModel):
    """Details of a moderation failure, when available."""
    code: Optional[str] = None
    message: str
    param: Optional[str] = None
    type: str
    moderation_details: Optional[ImageGenerationCallErrorModerationDetails] = None

class ImageGenerationCall(BaseModel):
    """An image generation request made by the model."""
    id: str
    result: Optional[str] = None
    status: Literal['in_progress', 'completed', 'generating', 'failed']
    type: Literal['image_generation_call']
    action: Optional[Literal['generate', 'edit', 'auto']] = None
    background: Optional[Literal['transparent', 'opaque', 'auto']] = None
    error: Optional[ImageGenerationCallError] = None
    output_format: Optional[Literal['png', 'webp', 'jpeg']] = None
    quality: Optional[Literal['low', 'medium', 'high', 'xhigh', 'max', 'auto']] = None
    revised_prompt: Optional[str] = None
    size: Union[str, Literal['1024x1024', '1024x1536', '1536x1024'], None] = None

class LocalShellCallAction(BaseModel):
    """Execute a shell command on the server."""
    command: List[str]
    env: Dict[str, str]
    type: Literal['exec']
    timeout_ms: Optional[int] = None
    user: Optional[str] = None
    working_directory: Optional[str] = None

class LocalShellCall(BaseModel):
    """A tool call to run a command on the local shell."""
    id: str
    action: LocalShellCallAction
    call_id: str
    status: Literal['in_progress', 'completed', 'incomplete']
    type: Literal['local_shell_call']

class LocalShellCallOutput(BaseModel):
    """The output of a local shell tool call."""
    id: str
    output: str
    type: Literal['local_shell_call_output']
    status: Optional[Literal['in_progress', 'completed', 'incomplete']] = None

class McpCall(BaseModel):
    """An invocation of a tool on an MCP server."""
    id: str
    arguments: str
    name: str
    server_label: str
    type: Literal['mcp_call']
    approval_request_id: Optional[str] = None
    error: Optional[McpToolCallError] = None
    output: Optional[str] = None
    status: Optional[Literal['in_progress', 'completed', 'incomplete', 'calling', 'failed']] = None

class McpListToolsTool(BaseModel):
    """A tool available on an MCP server."""
    input_schema: object
    name: str
    annotations: Optional[object] = None
    description: Optional[str] = None

class McpListTools(BaseModel):
    """A list of tools available on an MCP server."""
    id: str
    server_label: str
    tools: List[McpListToolsTool]
    type: Literal['mcp_list_tools']
    error: Optional[str] = None

class McpApprovalRequest(BaseModel):
    """A request for human approval of a tool invocation."""
    id: str
    arguments: str
    name: str
    server_label: str
    type: Literal['mcp_approval_request']

class McpApprovalResponse(BaseModel):
    """A response to an MCP approval request."""
    id: str
    approval_request_id: str
    approve: bool
    type: Literal['mcp_approval_response']
    reason: Optional[str] = None
ResponseOutputItem: TypeAlias = Annotated[Union[ResponseOutputMessage, ResponseFileSearchToolCall, ResponseFunctionToolCall, ResponseFunctionToolCallOutputItem, ResponseFunctionWebSearch, ResponseComputerToolCall, ResponseComputerToolCallOutputItem, ResponseReasoningItem, Program, ProgramOutput, ResponseToolSearchCall, ResponseToolSearchOutputItem, AdditionalTools, ResponseCompactionItem, ImageGenerationCall, ResponseCodeInterpreterToolCall, LocalShellCall, LocalShellCallOutput, ResponseFunctionShellToolCall, ResponseFunctionShellToolCallOutput, ResponseApplyPatchToolCall, ResponseApplyPatchToolCallOutput, McpCall, McpListTools, McpApprovalRequest, McpApprovalResponse, ResponseCustomToolCall, ResponseCustomToolCallOutputItem], PropertyInfo(discriminator='type')]
