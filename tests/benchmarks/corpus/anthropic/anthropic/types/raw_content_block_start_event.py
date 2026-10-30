
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Literal, Annotated, TypeAlias
from .._models import BaseModel, UnionDiscriminator
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
ContentBlock: TypeAlias = Annotated[Union[TextBlock, ThinkingBlock, RedactedThinkingBlock, ToolUseBlock, ServerToolUseBlock, WebSearchToolResultBlock, WebFetchToolResultBlock, CodeExecutionToolResultBlock, BashCodeExecutionToolResultBlock, TextEditorCodeExecutionToolResultBlock, ToolSearchToolResultBlock, ContainerUploadBlock], UnionDiscriminator('type')]

class RawContentBlockStartEvent(BaseModel):
    content_block: ContentBlock
    index: int
    type: Literal['content_block_start']
