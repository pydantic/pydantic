
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from .._models import BaseModel
from .tool_use_caller import ToolUseCaller
from .browser_switch_tab_input import BrowserSwitchTabInput

class BrowserSwitchTabToolUseBlock(BaseModel):
    id: str
    caller: ToolUseCaller
    input: BrowserSwitchTabInput
    name: Literal['switch_tab']
    toolset_name: Literal['browser']
    type: Literal['tool_use']
