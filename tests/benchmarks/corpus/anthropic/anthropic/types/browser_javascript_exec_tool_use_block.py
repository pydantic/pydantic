
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from .._models import BaseModel
from .tool_use_caller import ToolUseCaller
from .browser_javascript_exec_input import BrowserJavascriptExecInput

class BrowserJavascriptExecToolUseBlock(BaseModel):
    id: str
    caller: ToolUseCaller
    input: BrowserJavascriptExecInput
    name: Literal['javascript_exec']
    toolset_name: Literal['browser']
    type: Literal['tool_use']
