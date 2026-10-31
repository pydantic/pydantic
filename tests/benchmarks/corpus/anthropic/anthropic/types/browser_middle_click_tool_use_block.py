
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from .._models import BaseModel
from .tool_use_caller import ToolUseCaller
from .browser_middle_click_input import BrowserMiddleClickInput

class BrowserMiddleClickToolUseBlock(BaseModel):
    id: str
    caller: ToolUseCaller
    input: BrowserMiddleClickInput
    name: Literal['middle_click']
    toolset_name: Literal['browser']
    type: Literal['tool_use']
