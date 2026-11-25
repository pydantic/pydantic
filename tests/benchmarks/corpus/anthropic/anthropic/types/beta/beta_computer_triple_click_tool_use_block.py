
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel
from .beta_tool_use_caller import BetaToolUseCaller
from .beta_computer_triple_click_input import BetaComputerTripleClickInput

class BetaComputerTripleClickToolUseBlock(BaseModel):
    id: str
    input: BetaComputerTripleClickInput
    name: Literal['triple_click']
    toolset_name: Literal['computer']
    type: Literal['tool_use']
    caller: Optional[BetaToolUseCaller] = None
