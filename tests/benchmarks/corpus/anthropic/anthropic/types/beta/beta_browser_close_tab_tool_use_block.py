
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel
from .beta_tool_use_caller import BetaToolUseCaller
from .beta_browser_close_tab_input import BetaBrowserCloseTabInput

class BetaBrowserCloseTabToolUseBlock(BaseModel):
    id: str
    input: BetaBrowserCloseTabInput
    name: Literal['close_tab']
    toolset_name: Literal['browser']
    type: Literal['tool_use']
    caller: Optional[BetaToolUseCaller] = None
