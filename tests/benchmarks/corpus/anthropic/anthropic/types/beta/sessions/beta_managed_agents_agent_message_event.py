
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import List, Union
from datetime import datetime
from typing_extensions import Literal, Annotated, TypeAlias
from ...._models import BaseModel, UnionDiscriminator
from .beta_managed_agents_text_block import BetaManagedAgentsTextBlock
from .beta_managed_agents_redacted_block import BetaManagedAgentsRedactedBlock
Content: TypeAlias = Annotated[Union[BetaManagedAgentsTextBlock, BetaManagedAgentsRedactedBlock], UnionDiscriminator('type')]

class BetaManagedAgentsAgentMessageEvent(BaseModel):
    """An agent response event in the session conversation."""
    id: str
    content: List[Content]
    processed_at: datetime
    type: Literal['agent.message']
