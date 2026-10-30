
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from .._models import BaseModel
from .tool_use_caller import ToolUseCaller
from .browser_list_tabs_input import BrowserListTabsInput

class BrowserListTabsToolUseBlock(BaseModel):
    id: str
    caller: ToolUseCaller
    input: BrowserListTabsInput
    name: Literal['list_tabs']
    toolset_name: Literal['browser']
    type: Literal['tool_use']
