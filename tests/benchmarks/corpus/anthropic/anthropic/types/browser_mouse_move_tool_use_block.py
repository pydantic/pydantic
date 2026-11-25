
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from .._models import BaseModel
from .tool_use_caller import ToolUseCaller
from .browser_mouse_move_input import BrowserMouseMoveInput

class BrowserMouseMoveToolUseBlock(BaseModel):
    id: str
    caller: ToolUseCaller
    input: BrowserMouseMoveInput
    name: Literal['mouse_move']
    toolset_name: Literal['browser']
    type: Literal['tool_use']
