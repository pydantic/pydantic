
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel
from .beta_web_search_tool_result_error_code import BetaWebSearchToolResultErrorCode

class BetaWebSearchToolResultError(BaseModel):
    error_code: BetaWebSearchToolResultErrorCode
    type: Literal['web_search_tool_result_error']
