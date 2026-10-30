
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from .._models import BaseModel
from .bash_code_execution_tool_result_error_code import BashCodeExecutionToolResultErrorCode

class BashCodeExecutionToolResultError(BaseModel):
    error_code: BashCodeExecutionToolResultErrorCode
    type: Literal['bash_code_execution_tool_result_error']
