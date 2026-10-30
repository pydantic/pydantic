
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import List, Union, Optional
from datetime import datetime
from typing_extensions import Literal, Annotated, TypeAlias
from ..._models import BaseModel, UnionDiscriminator
from .sessions.beta_managed_agents_text_block import BetaManagedAgentsTextBlock
from .sessions.beta_managed_agents_image_block import BetaManagedAgentsImageBlock
from .sessions.beta_managed_agents_document_block import BetaManagedAgentsDocumentBlock
from .sessions.beta_managed_agents_search_result_block import BetaManagedAgentsSearchResultBlock
Content: TypeAlias = Annotated[Union[BetaManagedAgentsTextBlock, BetaManagedAgentsImageBlock, BetaManagedAgentsDocumentBlock, BetaManagedAgentsSearchResultBlock], UnionDiscriminator('type')]

class BetaManagedAgentsUserToolResultEvent(BaseModel):
    """Event sent by the client providing the result of an agent-toolset tool execution.

    Only valid on `self_hosted` environments, where sandbox-routed tools are executed by the client rather than the server.
    """
    id: str
    tool_use_id: str
    type: Literal['user.tool_result']
    content: Optional[List[Content]] = None
    is_error: Optional[bool] = None
    processed_at: Optional[datetime] = None
    session_thread_id: Optional[str] = None
