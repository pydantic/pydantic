
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel
from .beta_response_tool_union import BetaResponseToolUnion

class BetaToolChangeToolDefinition(BaseModel):
    """
    A tool defined by value, as a `compaction` block's `tool_changes` entry
    reports it: `definition` is the tool's definition as it was sent, in the
    form of a `tools` entry, without `cache_control`. Send it back unchanged
    with the block.
    """
    definition: BetaResponseToolUnion
    type: Literal['tool_definition']
