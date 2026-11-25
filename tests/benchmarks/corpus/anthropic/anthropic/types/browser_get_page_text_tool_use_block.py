
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from .._models import BaseModel
from .tool_use_caller import ToolUseCaller
from .browser_get_page_text_input import BrowserGetPageTextInput

class BrowserGetPageTextToolUseBlock(BaseModel):
    id: str
    caller: ToolUseCaller
    input: BrowserGetPageTextInput
    name: Literal['get_page_text']
    toolset_name: Literal['browser']
    type: Literal['tool_use']
