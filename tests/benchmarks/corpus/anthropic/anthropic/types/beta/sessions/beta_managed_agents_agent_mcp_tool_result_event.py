
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import List, Union, Optional
from datetime import datetime
from typing_extensions import Literal, Annotated, TypeAlias
from ...._models import BaseModel, UnionDiscriminator
from .beta_managed_agents_text_block import BetaManagedAgentsTextBlock
from .beta_managed_agents_image_block import BetaManagedAgentsImageBlock
from .beta_managed_agents_document_block import BetaManagedAgentsDocumentBlock
from .beta_managed_agents_search_result_block import BetaManagedAgentsSearchResultBlock
Content: TypeAlias = Annotated[Union[BetaManagedAgentsTextBlock, BetaManagedAgentsImageBlock, BetaManagedAgentsDocumentBlock, BetaManagedAgentsSearchResultBlock], UnionDiscriminator('type')]

class BetaManagedAgentsAgentMCPToolResultEvent(BaseModel):
    """Event representing the result of an MCP tool execution."""
    id: str
    mcp_tool_use_id: str
    processed_at: datetime
    type: Literal['agent.mcp_tool_result']
    content: Optional[List[Content]] = None
    is_error: Optional[bool] = None
