
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Literal, Annotated, TypeAlias
from ..._models import BaseModel, UnionDiscriminator
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
ContentBlock: TypeAlias = Annotated[Union[BetaTextBlock, BetaThinkingBlock, BetaRedactedThinkingBlock, BetaToolUseBlock, BetaServerToolUseBlock, BetaWebSearchToolResultBlock, BetaWebFetchToolResultBlock, BetaAdvisorToolResultBlock, BetaCodeExecutionToolResultBlock, BetaBashCodeExecutionToolResultBlock, BetaTextEditorCodeExecutionToolResultBlock, BetaToolSearchToolResultBlock, BetaMCPToolUseBlock, BetaMCPToolResultBlock, BetaContainerUploadBlock, BetaCompactionBlock, BetaFallbackBlock, BetaMCPToolListingBlock], UnionDiscriminator('type')]

class BetaRawContentBlockStartEvent(BaseModel):
    content_block: ContentBlock
    index: int
    type: Literal['content_block_start']
