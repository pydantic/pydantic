
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel
from .beta_code_execution_tool_result_error_code import BetaCodeExecutionToolResultErrorCode

class BetaCodeExecutionToolResultError(BaseModel):
    error_code: BetaCodeExecutionToolResultErrorCode
    type: Literal['code_execution_tool_result_error']
