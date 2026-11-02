
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from .._models import BaseModel
from .tool_use_caller import ToolUseCaller
from .browser_type_input import BrowserTypeInput

class BrowserTypeToolUseBlock(BaseModel):
    id: str
    caller: ToolUseCaller
    input: BrowserTypeInput
    name: Literal['type']
    toolset_name: Literal['browser']
    type: Literal['tool_use']
