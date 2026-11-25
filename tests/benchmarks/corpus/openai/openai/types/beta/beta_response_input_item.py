# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Dict, List, Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias
from ..._utils import PropertyInfo
from ..._models import BaseModel
from .beta_tool import BetaTool
from .beta_local_environment import BetaLocalEnvironment
from .beta_easy_input_message import BetaEasyInputMessage
from .beta_container_reference import BetaContainerReference
from .beta_mcp_tool_call_error import BetaMcpToolCallError
from .beta_response_output_message import BetaResponseOutputMessage
from .beta_response_reasoning_item import BetaResponseReasoningItem
from .beta_response_custom_tool_call import BetaResponseCustomToolCall
from .beta_response_computer_tool_call import BetaResponseComputerToolCall
from .beta_response_function_tool_call import BetaResponseFunctionToolCall
from .beta_response_input_text_content import BetaResponseInputTextContent
from .beta_response_function_web_search import BetaResponseFunctionWebSearch
from .beta_response_input_image_content import BetaResponseInputImageContent
from .beta_response_compaction_item_param import BetaResponseCompactionItemParam
from .beta_response_file_search_tool_call import BetaResponseFileSearchToolCall
from .beta_response_custom_tool_call_output import BetaResponseCustomToolCallOutput
from .beta_response_code_interpreter_tool_call import BetaResponseCodeInterpreterToolCall
from .beta_response_input_message_content_list import BetaResponseInputMessageContentList
from .beta_response_tool_search_output_item_param import BetaResponseToolSearchOutputItemParam
from .beta_response_function_call_output_item_list import BetaResponseFunctionCallOutputItemList
from .beta_response_configuration_update_item_param import BetaResponseConfigurationUpdateItemParam
from .beta_response_function_shell_call_output_content import BetaResponseFunctionShellCallOutputContent
from .beta_response_computer_tool_call_output_screenshot import BetaResponseComputerToolCallOutputScreenshot

class MessageAgent(BaseModel):
    """The agent that produced this item."""
    agent_name: str

class Message(BaseModel):
    """
    A message input to the model with a role indicating instruction following
    hierarchy. Instructions given with the `developer` or `system` role take
    precedence over instructions given with the `user` role.
    """
    content: BetaResponseInputMessageContentList
    role: Literal['user', 'system', 'developer']
    agent: Optional[MessageAgent] = None
    status: Optional[Literal['in_progress', 'completed', 'incomplete']] = None
    type: Optional[Literal['message']] = None

class ComputerCallOutputAcknowledgedSafetyCheck(BaseModel):
    """A pending safety check for the computer call."""
    id: str
    code: Optional[str] = None
    message: Optional[str] = None

class ComputerCallOutputAgent(BaseModel):
    """The agent that produced this item."""
    agent_name: str

class ComputerCallOutput(BaseModel):
    """The output of a computer tool call."""
    call_id: str
    output: BetaResponseComputerToolCallOutputScreenshot
    type: Literal['computer_call_output']
    id: Optional[str] = None
    acknowledged_safety_checks: Optional[List[ComputerCallOutputAcknowledgedSafetyCheck]] = None
    agent: Optional[ComputerCallOutputAgent] = None
    status: Optional[Literal['in_progress', 'completed', 'incomplete']] = None

class FunctionCallOutputAgent(BaseModel):
    """The agent that produced this item."""
    agent_name: str

class FunctionCallOutputCallerDirect(BaseModel):
    type: Literal['direct']

class FunctionCallOutputCallerProgram(BaseModel):
    caller_id: str
    type: Literal['program']
FunctionCallOutputCaller: TypeAlias = Annotated[Union[FunctionCallOutputCallerDirect, FunctionCallOutputCallerProgram, None], PropertyInfo(discriminator='type')]

class FunctionCallOutput(BaseModel):
    """The output of a function tool call."""
    output: Union[str, BetaResponseFunctionCallOutputItemList]
    type: Literal['function_call_output']
    id: Optional[str] = None
    agent: Optional[FunctionCallOutputAgent] = None
    call_id: Optional[str] = None
    caller: Optional[FunctionCallOutputCaller] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    status: Optional[Literal['in_progress', 'completed', 'incomplete']] = None

class AgentMessageContentEncryptedContent(BaseModel):
    """
    Opaque encrypted content that Responses API decrypts inside trusted model execution.
    """
    encrypted_content: str
    type: Literal['encrypted_content']
AgentMessageContent: TypeAlias = Annotated[Union[BetaResponseInputTextContent, BetaResponseInputImageContent, AgentMessageContentEncryptedContent], PropertyInfo(discriminator='type')]

class AgentMessageAgent(BaseModel):
    """The agent that produced this item."""
    agent_name: str

class AgentMessage(BaseModel):
    """A message routed between agents."""
    author: str
    content: List[AgentMessageContent]
    recipient: str
    type: Literal['agent_message']
    id: Optional[str] = None
    agent: Optional[AgentMessageAgent] = None

class MultiAgentCallAgent(BaseModel):
    """The agent that produced this item."""
    agent_name: str

class MultiAgentCall(BaseModel):
    action: Literal['spawn_agent', 'interrupt_agent', 'list_agents', 'send_message', 'followup_task', 'wait_agent']
    arguments: str
    call_id: str
    type: Literal['multi_agent_call']
    id: Optional[str] = None
    agent: Optional[MultiAgentCallAgent] = None

class MultiAgentCallOutputOutputAnnotationFileCitation(BaseModel):
    file_id: str
    filename: str
    index: int
    type: Literal['file_citation']

class MultiAgentCallOutputOutputAnnotationURLCitation(BaseModel):
    end_index: int
    start_index: int
    title: str
    type: Literal['url_citation']
    url: str

class MultiAgentCallOutputOutputAnnotationContainerFileCitation(BaseModel):
    container_id: str
    end_index: int
    file_id: str
    filename: str
    start_index: int
    type: Literal['container_file_citation']
MultiAgentCallOutputOutputAnnotation: TypeAlias = Annotated[Union[MultiAgentCallOutputOutputAnnotationFileCitation, MultiAgentCallOutputOutputAnnotationURLCitation, MultiAgentCallOutputOutputAnnotationContainerFileCitation], PropertyInfo(discriminator='type')]

class MultiAgentCallOutputOutput(BaseModel):
    text: str
    type: Literal['output_text']
    annotations: Optional[List[MultiAgentCallOutputOutputAnnotation]] = None

class MultiAgentCallOutputAgent(BaseModel):
    """The agent that produced this item."""
    agent_name: str

class MultiAgentCallOutput(BaseModel):
    action: Literal['spawn_agent', 'interrupt_agent', 'list_agents', 'send_message', 'followup_task', 'wait_agent']
    call_id: str
    output: List[MultiAgentCallOutputOutput]
    type: Literal['multi_agent_call_output']
    id: Optional[str] = None
    agent: Optional[MultiAgentCallOutputAgent] = None

class ToolSearchCallAgent(BaseModel):
    """The agent that produced this item."""
    agent_name: str

class ToolSearchCall(BaseModel):
    arguments: object
    type: Literal['tool_search_call']
    id: Optional[str] = None
    agent: Optional[ToolSearchCallAgent] = None
    call_id: Optional[str] = None
    execution: Optional[Literal['server', 'client']] = None
    status: Optional[Literal['in_progress', 'completed', 'incomplete']] = None

class AdditionalToolsAgent(BaseModel):
    """The agent that produced this item."""
    agent_name: str

class AdditionalTools(BaseModel):
    role: Literal['developer']
    tools: List[BetaTool]
    type: Literal['additional_tools']
    id: Optional[str] = None
    agent: Optional[AdditionalToolsAgent] = None

class ImageGenerationCallAgent(BaseModel):
    """The agent that produced this item."""
    agent_name: str

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
    agent: Optional[ImageGenerationCallAgent] = None
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

class LocalShellCallAgent(BaseModel):
    """The agent that produced this item."""
    agent_name: str

class LocalShellCall(BaseModel):
    """A tool call to run a command on the local shell."""
    id: str
    action: LocalShellCallAction
    call_id: str
    status: Literal['in_progress', 'completed', 'incomplete']
    type: Literal['local_shell_call']
    agent: Optional[LocalShellCallAgent] = None

class LocalShellCallOutputAgent(BaseModel):
    """The agent that produced this item."""
    agent_name: str

class LocalShellCallOutput(BaseModel):
    """The output of a local shell tool call."""
    id: str
    output: str
    type: Literal['local_shell_call_output']
    agent: Optional[LocalShellCallOutputAgent] = None
    status: Optional[Literal['in_progress', 'completed', 'incomplete']] = None

class ShellCallAction(BaseModel):
    """The shell commands and limits that describe how to run the tool call."""
    commands: List[str]
    max_output_length: Optional[int] = None
    timeout_ms: Optional[int] = None

class ShellCallAgent(BaseModel):
    """The agent that produced this item."""
    agent_name: str

class ShellCallCallerDirect(BaseModel):
    type: Literal['direct']

class ShellCallCallerProgram(BaseModel):
    caller_id: str
    type: Literal['program']
ShellCallCaller: TypeAlias = Annotated[Union[ShellCallCallerDirect, ShellCallCallerProgram, None], PropertyInfo(discriminator='type')]
ShellCallEnvironment: TypeAlias = Annotated[Union[BetaLocalEnvironment, BetaContainerReference, None], PropertyInfo(discriminator='type')]

class ShellCall(BaseModel):
    """A tool representing a request to execute one or more shell commands."""
    action: ShellCallAction
    call_id: str
    type: Literal['shell_call']
    id: Optional[str] = None
    agent: Optional[ShellCallAgent] = None
    caller: Optional[ShellCallCaller] = None
    environment: Optional[ShellCallEnvironment] = None
    status: Optional[Literal['in_progress', 'completed', 'incomplete']] = None

class ShellCallOutputAgent(BaseModel):
    """The agent that produced this item."""
    agent_name: str

class ShellCallOutputCallerDirect(BaseModel):
    type: Literal['direct']

class ShellCallOutputCallerProgram(BaseModel):
    caller_id: str
    type: Literal['program']
ShellCallOutputCaller: TypeAlias = Annotated[Union[ShellCallOutputCallerDirect, ShellCallOutputCallerProgram, None], PropertyInfo(discriminator='type')]

class ShellCallOutput(BaseModel):
    """The streamed output items emitted by a shell tool call."""
    call_id: str
    output: List[BetaResponseFunctionShellCallOutputContent]
    type: Literal['shell_call_output']
    id: Optional[str] = None
    agent: Optional[ShellCallOutputAgent] = None
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

class ApplyPatchCallAgent(BaseModel):
    """The agent that produced this item."""
    agent_name: str

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
    agent: Optional[ApplyPatchCallAgent] = None
    caller: Optional[ApplyPatchCallCaller] = None

class ApplyPatchCallOutputAgent(BaseModel):
    """The agent that produced this item."""
    agent_name: str

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
    agent: Optional[ApplyPatchCallOutputAgent] = None
    caller: Optional[ApplyPatchCallOutputCaller] = None
    output: Optional[str] = None

class McpListToolsTool(BaseModel):
    """A tool available on an MCP server."""
    input_schema: object
    name: str
    annotations: Optional[object] = None
    description: Optional[str] = None

class McpListToolsAgent(BaseModel):
    """The agent that produced this item."""
    agent_name: str

class McpListTools(BaseModel):
    """A list of tools available on an MCP server."""
    id: str
    server_label: str
    tools: List[McpListToolsTool]
    type: Literal['mcp_list_tools']
    agent: Optional[McpListToolsAgent] = None
    error: Optional[str] = None

class McpApprovalRequestAgent(BaseModel):
    """The agent that produced this item."""
    agent_name: str

class McpApprovalRequest(BaseModel):
    """A request for human approval of a tool invocation."""
    id: str
    arguments: str
    name: str
    server_label: str
    type: Literal['mcp_approval_request']
    agent: Optional[McpApprovalRequestAgent] = None

class McpApprovalResponseAgent(BaseModel):
    """The agent that produced this item."""
    agent_name: str

class McpApprovalResponse(BaseModel):
    """A response to an MCP approval request."""
    approval_request_id: str
    approve: bool
    type: Literal['mcp_approval_response']
    id: Optional[str] = None
    agent: Optional[McpApprovalResponseAgent] = None
    reason: Optional[str] = None

class McpCallAgent(BaseModel):
    """The agent that produced this item."""
    agent_name: str

class McpCall(BaseModel):
    """An invocation of a tool on an MCP server."""
    id: str
    arguments: str
    name: str
    server_label: str
    type: Literal['mcp_call']
    agent: Optional[McpCallAgent] = None
    approval_request_id: Optional[str] = None
    error: Optional[BetaMcpToolCallError] = None
    output: Optional[str] = None
    status: Optional[Literal['in_progress', 'completed', 'incomplete', 'calling', 'failed']] = None

class CompactionTriggerAgent(BaseModel):
    """The agent that produced this item."""
    agent_name: str

class CompactionTrigger(BaseModel):
    """Compacts the current context. Must be the final input item."""
    type: Literal['compaction_trigger']
    id: Optional[str] = None
    agent: Optional[CompactionTriggerAgent] = None

class ItemReferenceAgent(BaseModel):
    """The agent that produced this item."""
    agent_name: str

class ItemReference(BaseModel):
    """An internal identifier for an item to reference."""
    id: str
    agent: Optional[ItemReferenceAgent] = None
    type: Optional[Literal['item_reference']] = None

class ProgramAgent(BaseModel):
    """The agent that produced this item."""
    agent_name: str

class Program(BaseModel):
    id: str
    call_id: str
    code: str
    fingerprint: str
    type: Literal['program']
    agent: Optional[ProgramAgent] = None

class ProgramOutputAgent(BaseModel):
    """The agent that produced this item."""
    agent_name: str

class ProgramOutput(BaseModel):
    id: str
    call_id: str
    result: str
    status: Literal['completed', 'incomplete']
    type: Literal['program_output']
    agent: Optional[ProgramOutputAgent] = None
BetaResponseInputItem: TypeAlias = Annotated[Union[BetaEasyInputMessage, Message, BetaResponseOutputMessage, BetaResponseFileSearchToolCall, BetaResponseComputerToolCall, ComputerCallOutput, BetaResponseFunctionWebSearch, BetaResponseFunctionToolCall, FunctionCallOutput, AgentMessage, MultiAgentCall, MultiAgentCallOutput, ToolSearchCall, BetaResponseToolSearchOutputItemParam, AdditionalTools, BetaResponseConfigurationUpdateItemParam, BetaResponseReasoningItem, BetaResponseCompactionItemParam, ImageGenerationCall, BetaResponseCodeInterpreterToolCall, LocalShellCall, LocalShellCallOutput, ShellCall, ShellCallOutput, ApplyPatchCall, ApplyPatchCallOutput, McpListTools, McpApprovalRequest, McpApprovalResponse, McpCall, BetaResponseCustomToolCallOutput, BetaResponseCustomToolCall, CompactionTrigger, ItemReference, Program, ProgramOutput], PropertyInfo(discriminator='type')]
