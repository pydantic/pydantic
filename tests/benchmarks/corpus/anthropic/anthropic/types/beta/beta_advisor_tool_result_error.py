
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class BetaAdvisorToolResultError(BaseModel):
    error_code: Literal['max_uses_exceeded', 'prompt_too_long', 'too_many_requests', 'overloaded', 'unavailable', 'execution_time_exceeded', 'model_not_found']
    type: Literal['advisor_tool_result_error']
