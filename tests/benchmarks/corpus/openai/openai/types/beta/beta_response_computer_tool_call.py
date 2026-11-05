# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Optional
from typing_extensions import Literal
from ..._models import BaseModel
from .beta_computer_action import BetaComputerAction
from .beta_computer_action_list import BetaComputerActionList

class PendingSafetyCheck(BaseModel):
    """A pending safety check for the computer call."""
    id: str
    code: Optional[str] = None
    message: Optional[str] = None

class Agent(BaseModel):
    """The agent that produced this item."""
    agent_name: str

class BetaResponseComputerToolCall(BaseModel):
    """A tool call to a computer use tool.

    See the
    [computer use guide](https://developers.openai.com/api/docs/guides/tools-computer-use) for more information.
    """
    id: str
    call_id: str
    pending_safety_checks: List[PendingSafetyCheck]
    status: Literal['in_progress', 'completed', 'incomplete']
    type: Literal['computer_call']
    action: Optional[BetaComputerAction] = None
    actions: Optional[BetaComputerActionList] = None
    agent: Optional[Agent] = None
