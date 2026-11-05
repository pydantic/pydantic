
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import List, Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias
from ..._models import BaseModel, UnionDiscriminator
from .beta_response_tool_removal_block import BetaResponseToolRemovalBlock
from .beta_response_tool_addition_block import BetaResponseToolAdditionBlock
ToolChange: TypeAlias = Annotated[Union[BetaResponseToolAdditionBlock, BetaResponseToolRemovalBlock], UnionDiscriminator('type')]

class BetaCompactionBlock(BaseModel):
    """A compaction block returned when autocompact is triggered.

    When content is None, it indicates the compaction failed to produce a valid
    summary (e.g., malformed output from the model). Clients may round-trip
    compaction blocks with null content; the server treats them as no-ops.
    """
    content: Optional[str] = None
    encrypted_content: Optional[str] = None
    type: Literal['compaction']
    signature: Optional[str] = None
    tool_changes: Optional[List[ToolChange]] = None
