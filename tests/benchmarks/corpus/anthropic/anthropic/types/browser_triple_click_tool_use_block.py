
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from .._models import BaseModel
from .tool_use_caller import ToolUseCaller
from .browser_triple_click_input import BrowserTripleClickInput

class BrowserTripleClickToolUseBlock(BaseModel):
    id: str
    caller: ToolUseCaller
    input: BrowserTripleClickInput
    name: Literal['triple_click']
    toolset_name: Literal['browser']
    type: Literal['tool_use']
