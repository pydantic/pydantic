
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class BetaClearThinking20251015EditResponse(BaseModel):
    cleared_input_tokens: int
    cleared_thinking_turns: int
    type: Literal['clear_thinking_20251015']
