
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from .._models import BaseModel
from .tool_use_caller import ToolUseCaller
from .browser_form_input_input import BrowserFormInputInput

class BrowserFormInputToolUseBlock(BaseModel):
    id: str
    caller: ToolUseCaller
    input: BrowserFormInputInput
    name: Literal['form_input']
    toolset_name: Literal['browser']
    type: Literal['tool_use']
