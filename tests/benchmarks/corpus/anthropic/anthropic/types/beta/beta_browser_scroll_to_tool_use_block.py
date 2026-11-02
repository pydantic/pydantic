
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel
from .beta_tool_use_caller import BetaToolUseCaller
from .beta_browser_scroll_to_input import BetaBrowserScrollToInput

class BetaBrowserScrollToToolUseBlock(BaseModel):
    id: str
    input: BetaBrowserScrollToInput
    name: Literal['scroll_to']
    toolset_name: Literal['browser']
    type: Literal['tool_use']
    caller: Optional[BetaToolUseCaller] = None
