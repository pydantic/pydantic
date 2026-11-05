
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel
from .beta_tool_use_caller import BetaToolUseCaller
from .beta_browser_hover_input import BetaBrowserHoverInput

class BetaBrowserHoverToolUseBlock(BaseModel):
    id: str
    input: BetaBrowserHoverInput
    name: Literal['hover']
    toolset_name: Literal['browser']
    type: Literal['tool_use']
    caller: Optional[BetaToolUseCaller] = None
