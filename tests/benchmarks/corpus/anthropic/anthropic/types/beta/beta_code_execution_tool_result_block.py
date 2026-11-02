
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel
from .beta_code_execution_tool_result_block_content import BetaCodeExecutionToolResultBlockContent

class BetaCodeExecutionToolResultBlock(BaseModel):
    content: BetaCodeExecutionToolResultBlockContent
    tool_use_id: str
    type: Literal['code_execution_tool_result']
