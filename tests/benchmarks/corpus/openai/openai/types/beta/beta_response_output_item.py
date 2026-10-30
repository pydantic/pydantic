# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Dict, List, Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias
from ..._utils import PropertyInfo
from ..._models import BaseModel
from .beta_tool import BetaTool
from .beta_image_detail import BetaImageDetail
from .beta_mcp_tool_call_error import BetaMcpToolCallError
from .beta_response_input_file import BetaResponseInputFile
from .beta_response_input_text import BetaResponseInputText
from .beta_response_input_image import BetaResponseInputImage
from .beta_response_output_text import BetaResponseOutputText
from .beta_response_output_message import BetaResponseOutputMessage
from .beta_response_output_refusal import BetaResponseOutputRefusal
from .beta_response_reasoning_item import BetaResponseReasoningItem
from .beta_response_compaction_item import BetaResponseCompactionItem
from .beta_response_custom_tool_call import BetaResponseCustomToolCall
from .beta_response_tool_search_call import BetaResponseToolSearchCall
from .beta_response_computer_tool_call import BetaResponseComputerToolCall
from .beta_response_function_tool_call import BetaResponseFunctionToolCall
from .beta_response_function_web_search import BetaResponseFunctionWebSearch
from .beta_response_apply_patch_tool_call import BetaResponseApplyPatchToolCall
from .beta_response_file_search_tool_call import BetaResponseFileSearchToolCall
from .beta_response_tool_search_output_item import BetaResponseToolSearchOutputItem
from .beta_response_function_shell_tool_call import BetaResponseFunctionShellToolCall
from .beta_response_code_interpreter_tool_call import BetaResponseCodeInterpreterToolCall
from .beta_response_apply_patch_tool_call_output import BetaResponseApplyPatchToolCallOutput
from .beta_response_custom_tool_call_output_item import BetaResponseCustomToolCallOutputItem
from .beta_response_computer_tool_call_output_item import BetaResponseComputerToolCallOutputItem
from .beta_response_function_tool_call_output_item import BetaResponseFunctionToolCallOutputItem
from .beta_response_function_shell_tool_call_output import BetaResponseFunctionShellToolCallOutput

class AgentMessageContentText(BaseModel):
    """A text content."""
    text: str
    type: Literal['text']

class AgentMessageContentSummaryText(BaseModel):
    """A summary text from the model."""
    text: str
    type: Literal['summary_text']

class AgentMessageContentReasoningText(BaseModel):
    """Reasoning text from the model."""
    text: str
    type: Literal['reasoning_text']

class AgentMessageContentComputerScreenshotPromptCacheBreakpoint(BaseModel):
    """Marks the exact end of a reusable prompt prefix.

    When `ttl` is omitted, the breakpoint inherits the request's `prompt_cache_options.ttl`; the boundary is not rounded to a token block.
    """
    mode: Literal['explicit']
    ttl: Optional[Literal['30m', '12h']] = None

class AgentMessageContentComputerScreenshot(BaseModel):
    """A screenshot of a computer."""
    detail: BetaImageDetail
    file_id: Optional[str] = None
    image_url: Optional[str] = None
    type: Literal['computer_screenshot']
    prompt_cache_breakpoint: Optional[AgentMessageContentComputerScreenshotPromptCacheBreakpoint] = None

class AgentMessageContentEncryptedContent(BaseModel):
    """
    Opaque encrypted content that Responses API decrypts inside trusted model execution.
    """
    encrypted_content: str
    type: Literal['encrypted_content']
AgentMessageContent: TypeAlias = Annotated[Union[BetaResponseInputText, BetaResponseOutputText, AgentMessageContentText, AgentMessageContentSummaryText, AgentMessageContentReasoningText, BetaResponseOutputRefusal, BetaResponseInputImage, AgentMessageContentComputerScreenshot, BetaResponseInputFile, AgentMessageContentEncryptedContent], PropertyInfo(discriminator='type')]

class AgentMessageAgent(BaseModel):
    """The agent that produced this item."""
    agent_name: str

class AgentMessage(BaseModel):
    id: str
    author: str
    content: List[AgentMessageContent]
    recipient: str
    type: Literal['agent_message']
    agent: Optional[AgentMessageAgent] = None

class MultiAgentCallAgent(BaseModel):
    """The agent that produced this item."""
    agent_name: str

class MultiAgentCall(BaseModel):
    id: str
    action: Literal['spawn_agent', 'interrupt_agent', 'list_agents', 'send_message', 'followup_task', 'wait_agent']
    arguments: str
    call_id: str
    type: Literal['multi_agent_call']
    agent: Optional[MultiAgentCallAgent] = None

class MultiAgentCallOutputAgent(BaseModel):
    """The agent that produced this item."""
    agent_name: str

class MultiAgentCallOutput(BaseModel):
    id: str
    action: Literal['spawn_agent', 'interrupt_agent', 'list_agents', 'send_message', 'followup_task', 'wait_agent']
    call_id: str
    output: List[BetaResponseOutputText]
    type: Literal['multi_agent_call_output']
    agent: Optional[MultiAgentCallOutputAgent] = None

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

class AdditionalToolsAgent(BaseModel):
    """The agent that produced this item."""
    agent_name: str

class AdditionalTools(BaseModel):
    id: str
    role: Literal['unknown', 'user', 'assistant', 'system', 'critic', 'discriminator', 'developer', 'tool']
    tools: List[BetaTool]
    type: Literal['additional_tools']
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
    id: str
    approval_request_id: str
    approve: bool
    type: Literal['mcp_approval_response']
    agent: Optional[McpApprovalResponseAgent] = None
    reason: Optional[str] = None
BetaResponseOutputItem: TypeAlias = Annotated[Union[BetaResponseOutputMessage, BetaResponseFileSearchToolCall, BetaResponseFunctionToolCall, BetaResponseFunctionToolCallOutputItem, AgentMessage, MultiAgentCall, MultiAgentCallOutput, BetaResponseFunctionWebSearch, BetaResponseComputerToolCall, BetaResponseComputerToolCallOutputItem, BetaResponseReasoningItem, Program, ProgramOutput, BetaResponseToolSearchCall, BetaResponseToolSearchOutputItem, AdditionalTools, BetaResponseCompactionItem, ImageGenerationCall, BetaResponseCodeInterpreterToolCall, LocalShellCall, LocalShellCallOutput, BetaResponseFunctionShellToolCall, BetaResponseFunctionShellToolCallOutput, BetaResponseApplyPatchToolCall, BetaResponseApplyPatchToolCallOutput, McpCall, McpListTools, McpApprovalRequest, McpApprovalResponse, BetaResponseCustomToolCall, BetaResponseCustomToolCallOutputItem], PropertyInfo(discriminator='type')]
