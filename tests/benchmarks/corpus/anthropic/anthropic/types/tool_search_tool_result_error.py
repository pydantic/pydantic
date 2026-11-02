
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from .._models import BaseModel
from .tool_search_tool_result_error_code import ToolSearchToolResultErrorCode

class ToolSearchToolResultError(BaseModel):
    error_code: ToolSearchToolResultErrorCode
    error_message: Optional[str] = None
    type: Literal['tool_search_tool_result_error']
