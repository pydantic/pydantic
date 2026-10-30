
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Literal, TypeAlias
from ..._models import BaseModel
from .beta_text_editor_code_execution_tool_result_error import BetaTextEditorCodeExecutionToolResultError
from .beta_text_editor_code_execution_view_result_block import BetaTextEditorCodeExecutionViewResultBlock
from .beta_text_editor_code_execution_create_result_block import BetaTextEditorCodeExecutionCreateResultBlock
from .beta_text_editor_code_execution_str_replace_result_block import BetaTextEditorCodeExecutionStrReplaceResultBlock
Content: TypeAlias = Union[BetaTextEditorCodeExecutionToolResultError, BetaTextEditorCodeExecutionViewResultBlock, BetaTextEditorCodeExecutionCreateResultBlock, BetaTextEditorCodeExecutionStrReplaceResultBlock]

class BetaTextEditorCodeExecutionToolResultBlock(BaseModel):
    content: Content
    tool_use_id: str
    type: Literal['text_editor_code_execution_tool_result']
