
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import List
from typing_extensions import Literal
from ..._models import BaseModel
from .beta_code_execution_output_block import BetaCodeExecutionOutputBlock

class BetaCodeExecutionResultBlock(BaseModel):
    content: List[BetaCodeExecutionOutputBlock]
    return_code: int
    stderr: str
    stdout: str
    type: Literal['code_execution_result']
