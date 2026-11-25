
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from .._models import BaseModel
from .code_execution_tool_result_error_code import CodeExecutionToolResultErrorCode

class CodeExecutionToolResultError(BaseModel):
    error_code: CodeExecutionToolResultErrorCode
    type: Literal['code_execution_tool_result_error']
