
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

class BetaManagedAgentsUserMessageEvent(BaseModel):
    """A user message event in the session conversation."""
    id: str
    content: List[Content]
    type: Literal['user.message']
    processed_at: Optional[datetime] = None
