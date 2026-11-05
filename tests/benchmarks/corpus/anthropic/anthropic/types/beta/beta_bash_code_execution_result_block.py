
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import List
from typing_extensions import Literal
from ..._models import BaseModel
from .beta_bash_code_execution_output_block import BetaBashCodeExecutionOutputBlock

class BetaBashCodeExecutionResultBlock(BaseModel):
    content: List[BetaBashCodeExecutionOutputBlock]
    return_code: int
    stderr: str
    stdout: str
    type: Literal['bash_code_execution_result']
