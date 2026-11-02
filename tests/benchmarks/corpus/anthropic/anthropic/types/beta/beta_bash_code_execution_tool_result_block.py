
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Literal, TypeAlias
from ..._models import BaseModel
from .beta_bash_code_execution_result_block import BetaBashCodeExecutionResultBlock
from .beta_bash_code_execution_tool_result_error import BetaBashCodeExecutionToolResultError
Content: TypeAlias = Union[BetaBashCodeExecutionToolResultError, BetaBashCodeExecutionResultBlock]

class BetaBashCodeExecutionToolResultBlock(BaseModel):
    content: Content
    tool_use_id: str
    type: Literal['bash_code_execution_tool_result']
