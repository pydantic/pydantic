
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import List, Union
from typing_extensions import Literal, Annotated, TypeAlias
from ..._models import BaseModel, UnionDiscriminator
from .sessions.beta_managed_agents_text_block import BetaManagedAgentsTextBlock
from .sessions.beta_managed_agents_image_block import BetaManagedAgentsImageBlock
from .sessions.beta_managed_agents_document_block import BetaManagedAgentsDocumentBlock
from .sessions.beta_managed_agents_redacted_block import BetaManagedAgentsRedactedBlock
Content: TypeAlias = Annotated[Union[BetaManagedAgentsTextBlock, BetaManagedAgentsImageBlock, BetaManagedAgentsDocumentBlock, BetaManagedAgentsRedactedBlock], UnionDiscriminator('type')]

class BetaManagedAgentsDeploymentUserMessageEvent(BaseModel):
    """A user message sent to the session."""
    content: List[Content]
    type: Literal['user.message']
