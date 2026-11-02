
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import List
from typing_extensions import Literal
from .._models import BaseModel
from .code_execution_output_block import CodeExecutionOutputBlock

class CodeExecutionResultBlock(BaseModel):
    content: List[CodeExecutionOutputBlock]
    return_code: int
    stderr: str
    stdout: str
    type: Literal['code_execution_result']
