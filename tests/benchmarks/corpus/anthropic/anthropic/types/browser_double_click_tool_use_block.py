
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from .._models import BaseModel
from .tool_use_caller import ToolUseCaller
from .browser_double_click_input import BrowserDoubleClickInput

class BrowserDoubleClickToolUseBlock(BaseModel):
    id: str
    caller: ToolUseCaller
    input: BrowserDoubleClickInput
    name: Literal['double_click']
    toolset_name: Literal['browser']
    type: Literal['tool_use']
