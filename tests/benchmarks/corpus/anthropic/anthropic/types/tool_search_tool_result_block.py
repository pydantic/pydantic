
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Literal, TypeAlias
from .._models import BaseModel
from .tool_search_tool_result_error import ToolSearchToolResultError
from .tool_search_tool_search_result_block import ToolSearchToolSearchResultBlock
Content: TypeAlias = Union[ToolSearchToolResultError, ToolSearchToolSearchResultBlock]

class ToolSearchToolResultBlock(BaseModel):
    content: Content
    tool_use_id: str
    type: Literal['tool_search_tool_result']
