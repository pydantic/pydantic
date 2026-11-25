
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from __future__ import annotations
from typing import List, Union, Generic, Optional
from typing_extensions import TypeVar, Annotated, TypeAlias
from pydantic import Field as FieldInfo
from ..._models import UnionDiscriminator
from .beta_message import BetaMessage
from .beta_text_block import BetaTextBlock
from .beta_fallback_block import BetaFallbackBlock
from .beta_thinking_block import BetaThinkingBlock
from .beta_tool_use_block import BetaToolUseBlock
from .beta_compaction_block import BetaCompactionBlock
from .beta_mcp_tool_use_block import BetaMCPToolUseBlock
from .beta_mcp_tool_result_block import BetaMCPToolResultBlock
from .beta_server_tool_use_block import BetaServerToolUseBlock
from .beta_container_upload_block import BetaContainerUploadBlock
from .beta_mcp_tool_listing_block import BetaMCPToolListingBlock
from .beta_redacted_thinking_block import BetaRedactedThinkingBlock
from .beta_advisor_tool_result_block import BetaAdvisorToolResultBlock
from .beta_web_fetch_tool_result_block import BetaWebFetchToolResultBlock
from .beta_web_search_tool_result_block import BetaWebSearchToolResultBlock
from .beta_tool_search_tool_result_block import BetaToolSearchToolResultBlock
from .beta_code_execution_tool_result_block import BetaCodeExecutionToolResultBlock
from .beta_bash_code_execution_tool_result_block import BetaBashCodeExecutionToolResultBlock
from .beta_text_editor_code_execution_tool_result_block import BetaTextEditorCodeExecutionToolResultBlock
ResponseFormatT = TypeVar('ResponseFormatT', default=None)

class ParsedBetaTextBlock(BetaTextBlock, Generic[ResponseFormatT]):
    parsed_output: Optional[ResponseFormatT] = FieldInfo(default=None, exclude=True)
    __api_exclude__ = {'parsed_output'}
ParsedBetaContentBlock: TypeAlias = Annotated[Union[ParsedBetaTextBlock[ResponseFormatT], BetaThinkingBlock, BetaRedactedThinkingBlock, BetaToolUseBlock, BetaServerToolUseBlock, BetaWebSearchToolResultBlock, BetaWebFetchToolResultBlock, BetaAdvisorToolResultBlock, BetaCodeExecutionToolResultBlock, BetaBashCodeExecutionToolResultBlock, BetaTextEditorCodeExecutionToolResultBlock, BetaToolSearchToolResultBlock, BetaMCPToolUseBlock, BetaMCPToolResultBlock, BetaContainerUploadBlock, BetaCompactionBlock, BetaMCPToolListingBlock, BetaFallbackBlock], UnionDiscriminator('type')]

class ParsedBetaMessage(BetaMessage, Generic[ResponseFormatT]):
    content: List[ParsedBetaContentBlock]
