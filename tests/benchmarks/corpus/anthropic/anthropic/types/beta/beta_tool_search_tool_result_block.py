
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Literal, TypeAlias
from ..._models import BaseModel
from .beta_tool_search_tool_result_error import BetaToolSearchToolResultError
from .beta_tool_search_tool_search_result_block import BetaToolSearchToolSearchResultBlock
Content: TypeAlias = Union[BetaToolSearchToolResultError, BetaToolSearchToolSearchResultBlock]

class BetaToolSearchToolResultBlock(BaseModel):
    content: Content
    tool_use_id: str
    type: Literal['tool_search_tool_result']
