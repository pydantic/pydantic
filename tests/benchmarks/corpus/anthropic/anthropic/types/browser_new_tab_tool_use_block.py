
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from .._models import BaseModel
from .tool_use_caller import ToolUseCaller
from .browser_new_tab_input import BrowserNewTabInput

class BrowserNewTabToolUseBlock(BaseModel):
    id: str
    caller: ToolUseCaller
    input: BrowserNewTabInput
    name: Literal['new_tab']
    toolset_name: Literal['browser']
    type: Literal['tool_use']
