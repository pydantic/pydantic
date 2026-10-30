
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Literal, Annotated, TypeAlias
from ..._models import BaseModel, UnionDiscriminator
from .beta_response_tool_change_tool_reference import BetaResponseToolChangeToolReference
from .beta_response_tool_change_mcp_tool_reference import BetaResponseToolChangeMCPToolReference
from .beta_response_tool_change_mcp_toolset_reference import BetaResponseToolChangeMCPToolsetReference
Tool: TypeAlias = Annotated[Union[BetaResponseToolChangeToolReference, BetaResponseToolChangeMCPToolReference, BetaResponseToolChangeMCPToolsetReference], UnionDiscriminator('type')]

class BetaResponseToolRemovalBlock(BaseModel):
    """
    An entry of a `compaction` block's `tool_changes`: a tool of the
    request's `tools` (or an MCP tool or toolset) that the compacted range
    withdrew. Send it back unchanged.
    """
    tool: Tool
    type: Literal['tool_removal']
