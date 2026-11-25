
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from .._models import BaseModel
from .tool_use_caller import ToolUseCaller
from .browser_left_mouse_up_input import BrowserLeftMouseUpInput

class BrowserLeftMouseUpToolUseBlock(BaseModel):
    id: str
    caller: ToolUseCaller
    input: BrowserLeftMouseUpInput
    name: Literal['left_mouse_up']
    toolset_name: Literal['browser']
    type: Literal['tool_use']
