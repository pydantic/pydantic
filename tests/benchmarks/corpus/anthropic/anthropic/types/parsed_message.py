
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from __future__ import annotations
from typing import List, Union, Generic, Optional
from typing_extensions import TypeVar, Annotated, TypeAlias
from pydantic import Field as FieldInfo
from .message import Message
from .._models import UnionDiscriminator
from .text_block import TextBlock
from .thinking_block import ThinkingBlock
from .tool_use_block import ToolUseBlock
from .server_tool_use_block import ServerToolUseBlock
from .container_upload_block import ContainerUploadBlock
from .redacted_thinking_block import RedactedThinkingBlock
from .web_fetch_tool_result_block import WebFetchToolResultBlock
from .web_search_tool_result_block import WebSearchToolResultBlock
from .tool_search_tool_result_block import ToolSearchToolResultBlock
from .code_execution_tool_result_block import CodeExecutionToolResultBlock
from .bash_code_execution_tool_result_block import BashCodeExecutionToolResultBlock
from .text_editor_code_execution_tool_result_block import TextEditorCodeExecutionToolResultBlock
ResponseFormatT = TypeVar('ResponseFormatT', default=None)

class ParsedTextBlock(TextBlock, Generic[ResponseFormatT]):
    parsed_output: Optional[ResponseFormatT] = FieldInfo(default=None, exclude=True)
    __api_exclude__ = {'parsed_output'}
ParsedContentBlock: TypeAlias = Annotated[Union[ParsedTextBlock[ResponseFormatT], ThinkingBlock, RedactedThinkingBlock, ToolUseBlock, ServerToolUseBlock, WebSearchToolResultBlock, WebFetchToolResultBlock, CodeExecutionToolResultBlock, BashCodeExecutionToolResultBlock, TextEditorCodeExecutionToolResultBlock, ToolSearchToolResultBlock, ContainerUploadBlock], UnionDiscriminator('type')]

class ParsedMessage(Message, Generic[ResponseFormatT]):
    content: List[ParsedContentBlock]
