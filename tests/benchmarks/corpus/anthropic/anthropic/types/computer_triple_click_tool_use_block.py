
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from .._models import BaseModel
from .tool_use_caller import ToolUseCaller
from .computer_triple_click_input import ComputerTripleClickInput

class ComputerTripleClickToolUseBlock(BaseModel):
    id: str
    caller: ToolUseCaller
    input: ComputerTripleClickInput
    name: Literal['triple_click']
    toolset_name: Literal['computer']
    type: Literal['tool_use']
