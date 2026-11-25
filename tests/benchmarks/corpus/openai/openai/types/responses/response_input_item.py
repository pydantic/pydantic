# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Dict, List, Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias
from .tool import Tool
from ..._utils import PropertyInfo
from ..._models import BaseModel
from .local_environment import LocalEnvironment
from .easy_input_message import EasyInputMessage
from .container_reference import ContainerReference
from .mcp_tool_call_error import McpToolCallError
from .response_output_message import ResponseOutputMessage
from .response_reasoning_item import ResponseReasoningItem
from .response_custom_tool_call import ResponseCustomToolCall
from .response_computer_tool_call import ResponseComputerToolCall
from .response_function_tool_call import ResponseFunctionToolCall
from .response_function_web_search import ResponseFunctionWebSearch
from .response_compaction_item_param import ResponseCompactionItemParam
from .response_file_search_tool_call import ResponseFileSearchToolCall
from .response_custom_tool_call_output import ResponseCustomToolCallOutput
from .response_code_interpreter_tool_call import ResponseCodeInterpreterToolCall
from .response_input_message_content_list import ResponseInputMessageContentList
from .response_tool_search_output_item_param import ResponseToolSearchOutputItemParam
from .response_function_call_output_item_list import ResponseFunctionCallOutputItemList
from .response_configuration_update_item_param import ResponseConfigurationUpdateItemParam
from .response_function_shell_call_output_content import ResponseFunctionShellCallOutputContent
from .response_computer_tool_call_output_screenshot import ResponseComputerToolCallOutputScreenshot

class Message(BaseModel):
    """
    A message input to the model with a role indicating instruction following
    hierarchy. Instructions given with the `developer` or `system` role take
    precedence over instructions given with the `user` role.
    """
    content: ResponseInputMessageContentList
    role: Literal['user', 'system', 'developer']
    status: Optional[Literal['in_progress', 'completed', 'incomplete']] = None
    type: Optional[Literal['message']] = None

class ComputerCallOutputAcknowledgedSafetyCheck(BaseModel):
    """A pending safety check for the computer call."""
    id: str
    code: Optional[str] = None
    message: Optional[str] = None

class ComputerCallOutput(BaseModel):
    """The output of a computer tool call."""
    call_id: str
    output: ResponseComputerToolCallOutputScreenshot
    type: Literal['computer_call_output']
    id: Optional[str] = None
    acknowledged_safety_checks: Optional[List[ComputerCallOutputAcknowledgedSafetyCheck]] = None
    status: Optional[Literal['in_progress', 'completed', 'incomplete']] = None

class FunctionCallOutputCallerDirect(BaseModel):
    type: Literal['direct']

class FunctionCallOutputCallerProgram(BaseModel):
    caller_id: str
    type: Literal['program']
FunctionCallOutputCaller: TypeAlias = Annotated[Union[FunctionCallOutputCallerDirect, FunctionCallOutputCallerProgram, None], PropertyInfo(discriminator='type')]

class FunctionCallOutput(BaseModel):
    """The output of a function tool call."""
    output: Union[str, ResponseFunctionCallOutputItemList]
    type: Literal['function_call_output']
    id: Optional[str] = None
    call_id: Optional[str] = None
    caller: Optional[FunctionCallOutputCaller] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    status: Optional[Literal['in_progress', 'completed', 'incomplete']] = None

class ToolSearchCall(BaseModel):
    arguments: object
    type: Literal['tool_search_call']
    id: Optional[str] = None
    call_id: Optional[str] = None
    execution: Optional[Literal['server', 'client']] = None
    status: Optional[Literal['in_progress', 'completed', 'incomplete']] = None

class AdditionalTools(BaseModel):
    role: Literal['developer']
    tools: List[Tool]
    type: Literal['additional_tools']
    id: Optional[str] = None

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

class ShellCallAction(BaseModel):
    """The shell commands and limits that describe how to run the tool call."""
    commands: List[str]
    max_output_length: Optional[int] = None
    timeout_ms: Optional[int] = None

class ShellCallCallerDirect(BaseModel):
    type: Literal['direct']

class ShellCallCallerProgram(BaseModel):
    caller_id: str
    type: Literal['program']
ShellCallCaller: TypeAlias = Annotated[Union[ShellCallCallerDirect, ShellCallCallerProgram, None], PropertyInfo(discriminator='type')]
ShellCallEnvironment: TypeAlias = Annotated[Union[LocalEnvironment, ContainerReference, None], PropertyInfo(discriminator='type')]

class ShellCall(BaseModel):
    """A tool representing a request to execute one or more shell commands."""
    action: ShellCallAction
    call_id: str
    type: Literal['shell_call']
    id: Optional[str] = None
    caller: Optional[ShellCallCaller] = None
    environment: Optional[ShellCallEnvironment] = None
    status: Optional[Literal['in_progress', 'completed', 'incomplete']] = None

class ShellCallOutputCallerDirect(BaseModel):
    type: Literal['direct']

class ShellCallOutputCallerProgram(BaseModel):
    caller_id: str
    type: Literal['program']
ShellCallOutputCaller: TypeAlias = Annotated[Union[ShellCallOutputCallerDirect, ShellCallOutputCallerProgram, None], PropertyInfo(discriminator='type')]

class ShellCallOutput(BaseModel):
    """The streamed output items emitted by a shell tool call."""
    call_id: str
    output: List[ResponseFunctionShellCallOutputContent]
    type: Literal['shell_call_output']
    id: Optional[str] = None
    caller: Optional[ShellCallOutputCaller] = None
    max_output_length: Optional[int] = None
    status: Optional[Literal['in_progress', 'completed', 'incomplete']] = None

class ApplyPatchCallOperationCreateFile(BaseModel):
    """Instruction for creating a new file via the apply_patch tool."""
    diff: str
    path: str
    type: Literal['create_file']

class ApplyPatchCallOperationDeleteFile(BaseModel):
    """Instruction for deleting an existing file via the apply_patch tool."""
    path: str
    type: Literal['delete_file']

class ApplyPatchCallOperationUpdateFile(BaseModel):
    """Instruction for updating an existing file via the apply_patch tool."""
    diff: str
    path: str
    type: Literal['update_file']
ApplyPatchCallOperation: TypeAlias = Annotated[Union[ApplyPatchCallOperationCreateFile, ApplyPatchCallOperationDeleteFile, ApplyPatchCallOperationUpdateFile], PropertyInfo(discriminator='type')]

class ApplyPatchCallCallerDirect(BaseModel):
    type: Literal['direct']

class ApplyPatchCallCallerProgram(BaseModel):
    caller_id: str
    type: Literal['program']
ApplyPatchCallCaller: TypeAlias = Annotated[Union[ApplyPatchCallCallerDirect, ApplyPatchCallCallerProgram, None], PropertyInfo(discriminator='type')]

class ApplyPatchCall(BaseModel):
    """
    A tool call representing a request to create, delete, or update files using diff patches.
    """
    call_id: str
    operation: ApplyPatchCallOperation
    status: Literal['in_progress', 'completed']
    type: Literal['apply_patch_call']
    id: Optional[str] = None
    caller: Optional[ApplyPatchCallCaller] = None

class ApplyPatchCallOutputCallerDirect(BaseModel):
    type: Literal['direct']

class ApplyPatchCallOutputCallerProgram(BaseModel):
    caller_id: str
    type: Literal['program']
ApplyPatchCallOutputCaller: TypeAlias = Annotated[Union[ApplyPatchCallOutputCallerDirect, ApplyPatchCallOutputCallerProgram, None], PropertyInfo(discriminator='type')]

class ApplyPatchCallOutput(BaseModel):
    """The streamed output emitted by an apply patch tool call."""
    call_id: str
    status: Literal['completed', 'failed']
    type: Literal['apply_patch_call_output']
    id: Optional[str] = None
    caller: Optional[ApplyPatchCallOutputCaller] = None
    output: Optional[str] = None

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
    approval_request_id: str
    approve: bool
    type: Literal['mcp_approval_response']
    id: Optional[str] = None
    reason: Optional[str] = None

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

class CompactionTrigger(BaseModel):
    """Compacts the current context. Must be the final input item."""
    type: Literal['compaction_trigger']
    id: Optional[str] = None

class ItemReference(BaseModel):
    """An internal identifier for an item to reference."""
    id: str
    type: Optional[Literal['item_reference']] = None

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
ResponseInputItem: TypeAlias = Annotated[Union[EasyInputMessage, Message, ResponseOutputMessage, ResponseFileSearchToolCall, ResponseComputerToolCall, ComputerCallOutput, ResponseFunctionWebSearch, ResponseFunctionToolCall, FunctionCallOutput, ToolSearchCall, ResponseToolSearchOutputItemParam, AdditionalTools, ResponseConfigurationUpdateItemParam, ResponseReasoningItem, ResponseCompactionItemParam, ImageGenerationCall, ResponseCodeInterpreterToolCall, LocalShellCall, LocalShellCallOutput, ShellCall, ShellCallOutput, ApplyPatchCall, ApplyPatchCallOutput, McpListTools, McpApprovalRequest, McpApprovalResponse, McpCall, ResponseCustomToolCallOutput, ResponseCustomToolCall, CompactionTrigger, ItemReference, Program, ProgramOutput], PropertyInfo(discriminator='type')]
