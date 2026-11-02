
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from .._models import BaseModel
from .tool_use_caller import ToolUseCaller
from .browser_read_network_input import BrowserReadNetworkInput

class BrowserReadNetworkToolUseBlock(BaseModel):
    id: str
    caller: ToolUseCaller
    input: BrowserReadNetworkInput
    name: Literal['read_network']
    toolset_name: Literal['browser']
    type: Literal['tool_use']
