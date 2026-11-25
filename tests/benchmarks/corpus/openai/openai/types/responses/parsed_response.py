
# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Union, Generic, TypeVar, Optional
from typing_extensions import Annotated, TypeAlias
from ..._utils import PropertyInfo
from .response import Response
from ..._models import GenericModel
from .response_output_item import McpCall, Program, McpListTools, ProgramOutput, LocalShellCall, AdditionalTools, McpApprovalRequest, ImageGenerationCall, McpApprovalResponse, LocalShellCallAction, LocalShellCallOutput
from .response_output_text import ResponseOutputText
from .response_output_message import ResponseOutputMessage
from .response_output_refusal import ResponseOutputRefusal
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
ContentType = TypeVar('ContentType')

class ParsedResponseOutputText(ResponseOutputText, GenericModel, Generic[ContentType]):
    parsed: Optional[ContentType] = None
ParsedContent: TypeAlias = Annotated[Union[ParsedResponseOutputText[ContentType], ResponseOutputRefusal], PropertyInfo(discriminator='type')]

class ParsedResponseOutputMessage(ResponseOutputMessage, GenericModel, Generic[ContentType]):
    content: List[ParsedContent]

class ParsedResponseFunctionToolCall(ResponseFunctionToolCall):
    parsed_arguments: object = None
    __api_exclude__ = {'parsed_arguments'}
ParsedResponseOutputItem: TypeAlias = Annotated[Union[ParsedResponseOutputMessage[ContentType], ParsedResponseFunctionToolCall, ResponseFileSearchToolCall, ResponseFunctionWebSearch, ResponseComputerToolCall, ResponseComputerToolCallOutputItem, ResponseToolSearchCall, ResponseToolSearchOutputItem, AdditionalTools, ResponseReasoningItem, Program, ProgramOutput, McpCall, McpApprovalRequest, McpApprovalResponse, ImageGenerationCall, LocalShellCall, LocalShellCallOutput, LocalShellCallAction, McpListTools, ResponseCodeInterpreterToolCall, ResponseCompactionItem, ResponseFunctionShellToolCall, ResponseFunctionShellToolCallOutput, ResponseApplyPatchToolCall, ResponseApplyPatchToolCallOutput, ResponseFunctionToolCallOutputItem, ResponseCustomToolCall, ResponseCustomToolCallOutputItem], PropertyInfo(discriminator='type')]

class ParsedResponse(Response, GenericModel, Generic[ContentType]):
    output: List[ParsedResponseOutputItem]
