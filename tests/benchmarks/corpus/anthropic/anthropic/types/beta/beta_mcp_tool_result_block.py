
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import List, Union
from typing_extensions import Literal
from ..._models import BaseModel
from .beta_text_block import BetaTextBlock

class BetaMCPToolResultBlock(BaseModel):
    content: Union[str, List[BetaTextBlock]]
    is_error: bool
    tool_use_id: str
    type: Literal['mcp_tool_result']
