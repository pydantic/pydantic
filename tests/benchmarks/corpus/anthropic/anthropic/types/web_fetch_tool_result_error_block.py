
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from .._models import BaseModel
from .web_fetch_tool_result_error_code import WebFetchToolResultErrorCode

class WebFetchToolResultErrorBlock(BaseModel):
    error_code: WebFetchToolResultErrorCode
    type: Literal['web_fetch_tool_result_error']
