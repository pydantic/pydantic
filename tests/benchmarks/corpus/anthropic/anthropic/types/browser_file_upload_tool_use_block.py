
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from .._models import BaseModel
from .tool_use_caller import ToolUseCaller
from .browser_file_upload_input import BrowserFileUploadInput

class BrowserFileUploadToolUseBlock(BaseModel):
    id: str
    caller: ToolUseCaller
    input: BrowserFileUploadInput
    name: Literal['file_upload']
    toolset_name: Literal['browser']
    type: Literal['tool_use']
