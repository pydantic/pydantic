
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from .._models import BaseModel
from .tool_use_caller import ToolUseCaller
from .browser_left_mouse_down_input import BrowserLeftMouseDownInput

class BrowserLeftMouseDownToolUseBlock(BaseModel):
    id: str
    caller: ToolUseCaller
    input: BrowserLeftMouseDownInput
    name: Literal['left_mouse_down']
    toolset_name: Literal['browser']
    type: Literal['tool_use']
