# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias
from ..._utils import PropertyInfo
from ..._models import BaseModel

class Click(BaseModel):
    """A click action."""
    button: Literal['left', 'right', 'wheel', 'back', 'forward']
    type: Literal['click']
    x: int
    y: int
    keys: Optional[List[str]] = None

class DoubleClick(BaseModel):
    """A double click action."""
    keys: Optional[List[str]] = None
    type: Literal['double_click']
    x: int
    y: int

class DragPath(BaseModel):
    """An x/y coordinate pair, e.g. `{ x: 100, y: 200 }`."""
    x: int
    y: int

class Drag(BaseModel):
    """A drag action."""
    path: List[DragPath]
    type: Literal['drag']
    keys: Optional[List[str]] = None

class Keypress(BaseModel):
    """A collection of keypresses the model would like to perform."""
    keys: List[str]
    type: Literal['keypress']

class Move(BaseModel):
    """A mouse move action."""
    type: Literal['move']
    x: int
    y: int
    keys: Optional[List[str]] = None

class Screenshot(BaseModel):
    """A screenshot action."""
    type: Literal['screenshot']

class Scroll(BaseModel):
    """A scroll action."""
    scroll_x: int
    scroll_y: int
    type: Literal['scroll']
    x: int
    y: int
    keys: Optional[List[str]] = None

class Type(BaseModel):
    """An action to type in text."""
    text: str
    type: Literal['type']

class Wait(BaseModel):
    """A wait action."""
    type: Literal['wait']
ComputerAction: TypeAlias = Annotated[Union[Click, DoubleClick, Drag, Keypress, Move, Screenshot, Scroll, Type, Wait], PropertyInfo(discriminator='type')]
