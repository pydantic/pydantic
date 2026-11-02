
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from .._models import BaseModel

class TextEditorCodeExecutionViewResultBlock(BaseModel):
    content: str
    file_type: Literal['text', 'image', 'pdf']
    num_lines: Optional[int] = None
    start_line: Optional[int] = None
    total_lines: Optional[int] = None
    type: Literal['text_editor_code_execution_view_result']
