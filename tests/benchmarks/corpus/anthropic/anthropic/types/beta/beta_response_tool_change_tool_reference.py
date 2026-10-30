
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class BetaResponseToolChangeToolReference(BaseModel):
    """
    Reference to a single tool, by the name the model uses to call it, as
    a ``compaction`` block's ``tool_changes`` entry reports it: a tool
    declared in ``tools`` or defined by an earlier ``tool_addition`` block.
    Send it back unchanged with the block.
    """
    name: str
    type: Literal['tool_reference']
