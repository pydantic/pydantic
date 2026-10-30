
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from .._models import BaseModel
from .text_editor_code_execution_tool_result_error_code import TextEditorCodeExecutionToolResultErrorCode

class TextEditorCodeExecutionToolResultError(BaseModel):
    error_code: TextEditorCodeExecutionToolResultErrorCode
    error_message: Optional[str] = None
    type: Literal['text_editor_code_execution_tool_result_error']
