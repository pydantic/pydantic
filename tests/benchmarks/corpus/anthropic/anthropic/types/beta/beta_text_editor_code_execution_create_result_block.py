
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class BetaTextEditorCodeExecutionCreateResultBlock(BaseModel):
    is_file_update: bool
    type: Literal['text_editor_code_execution_create_result']
