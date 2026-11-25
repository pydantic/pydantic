
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import List, Union, Optional
from datetime import datetime
from typing_extensions import Literal, Annotated, TypeAlias
from ...._models import BaseModel, UnionDiscriminator
from .beta_managed_agents_text_block import BetaManagedAgentsTextBlock
from .beta_managed_agents_image_block import BetaManagedAgentsImageBlock
from .beta_managed_agents_document_block import BetaManagedAgentsDocumentBlock
from .beta_managed_agents_redacted_block import BetaManagedAgentsRedactedBlock
Content: TypeAlias = Annotated[Union[BetaManagedAgentsTextBlock, BetaManagedAgentsImageBlock, BetaManagedAgentsDocumentBlock, BetaManagedAgentsRedactedBlock], UnionDiscriminator('type')]

class BetaManagedAgentsAgentThreadMessageReceivedEvent(BaseModel):
    """
    Delivery event written to the target thread's input stream when an agent-to-agent message arrives.
    """
    id: str
    content: List[Content]
    from_session_thread_id: str
    processed_at: datetime
    type: Literal['agent.thread_message_received']
    from_agent_name: Optional[str] = None
