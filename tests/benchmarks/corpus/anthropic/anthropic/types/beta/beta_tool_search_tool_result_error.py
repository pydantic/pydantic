
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class BetaToolSearchToolResultError(BaseModel):
    error_code: Literal['invalid_tool_input', 'unavailable', 'too_many_requests', 'execution_time_exceeded']
    error_message: Optional[str] = None
    type: Literal['tool_search_tool_result_error']
