
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class BetaClearToolUses20250919EditResponse(BaseModel):
    cleared_input_tokens: int
    cleared_tool_uses: int
    type: Literal['clear_tool_uses_20250919']
