
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel
from .beta_tool_use_caller import BetaToolUseCaller
from .beta_browser_wait_input import BetaBrowserWaitInput

class BetaBrowserWaitToolUseBlock(BaseModel):
    id: str
    input: BetaBrowserWaitInput
    name: Literal['wait']
    toolset_name: Literal['browser']
    type: Literal['tool_use']
    caller: Optional[BetaToolUseCaller] = None
