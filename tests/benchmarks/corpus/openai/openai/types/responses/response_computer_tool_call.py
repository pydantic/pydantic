# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias
from ..._utils import PropertyInfo
from ..._models import BaseModel
from .computer_action_list import ComputerActionList

class PendingSafetyCheck(BaseModel):
    """A pending safety check for the computer call."""
    id: str
    code: Optional[str] = None
    message: Optional[str] = None

class ActionClick(BaseModel):
    """A click action."""
    button: Literal['left', 'right', 'wheel', 'back', 'forward']
    type: Literal['click']
    x: int
    y: int
    keys: Optional[List[str]] = None

class ActionDoubleClick(BaseModel):
    """A double click action."""
    keys: Optional[List[str]] = None
    type: Literal['double_click']
    x: int
    y: int

class ActionDragPath(BaseModel):
    """An x/y coordinate pair, e.g. `{ x: 100, y: 200 }`."""
    x: int
    y: int

class ActionDrag(BaseModel):
    """A drag action."""
    path: List[ActionDragPath]
    type: Literal['drag']
    keys: Optional[List[str]] = None

class ActionKeypress(BaseModel):
    """A collection of keypresses the model would like to perform."""
    keys: List[str]
    type: Literal['keypress']

class ActionMove(BaseModel):
    """A mouse move action."""
    type: Literal['move']
    x: int
    y: int
    keys: Optional[List[str]] = None

class ActionScreenshot(BaseModel):
    """A screenshot action."""
    type: Literal['screenshot']

class ActionScroll(BaseModel):
    """A scroll action."""
    scroll_x: int
    scroll_y: int
    type: Literal['scroll']
    x: int
    y: int
    keys: Optional[List[str]] = None

class ActionType(BaseModel):
    """An action to type in text."""
    text: str
    type: Literal['type']

class ActionWait(BaseModel):
    """A wait action."""
    type: Literal['wait']
Action: TypeAlias = Annotated[Union[ActionClick, ActionDoubleClick, ActionDrag, ActionKeypress, ActionMove, ActionScreenshot, ActionScroll, ActionType, ActionWait], PropertyInfo(discriminator='type')]

class ResponseComputerToolCall(BaseModel):
    """A tool call to a computer use tool.

    See the
    [computer use guide](https://developers.openai.com/api/docs/guides/tools-computer-use) for more information.
    """
    id: str
    call_id: str
    pending_safety_checks: List[PendingSafetyCheck]
    status: Literal['in_progress', 'completed', 'incomplete']
    type: Literal['computer_call']
    action: Optional[Action] = None
    actions: Optional[ComputerActionList] = None
