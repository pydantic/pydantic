
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from .._models import BaseModel
from .web_search_tool_result_error_code import WebSearchToolResultErrorCode

class WebSearchToolResultError(BaseModel):
    error_code: WebSearchToolResultErrorCode
    type: Literal['web_search_tool_result_error']
