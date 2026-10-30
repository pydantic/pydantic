
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from ..._models import BaseModel
from .beta_computer_key_config import BetaComputerKeyConfig
from .beta_computer_type_config import BetaComputerTypeConfig
from .beta_computer_wait_config import BetaComputerWaitConfig
from .beta_computer_zoom_config import BetaComputerZoomConfig
from .beta_computer_scroll_config import BetaComputerScrollConfig
from .beta_computer_hold_key_config import BetaComputerHoldKeyConfig
from .beta_computer_left_click_config import BetaComputerLeftClickConfig
from .beta_computer_mouse_move_config import BetaComputerMouseMoveConfig
from .beta_computer_screenshot_config import BetaComputerScreenshotConfig
from .beta_computer_right_click_config import BetaComputerRightClickConfig
from .beta_computer_double_click_config import BetaComputerDoubleClickConfig
from .beta_computer_middle_click_config import BetaComputerMiddleClickConfig
from .beta_computer_triple_click_config import BetaComputerTripleClickConfig
from .beta_computer_left_mouse_up_config import BetaComputerLeftMouseUpConfig
from .beta_computer_cursor_position_config import BetaComputerCursorPositionConfig
from .beta_computer_left_click_drag_config import BetaComputerLeftClickDragConfig
from .beta_computer_left_mouse_down_config import BetaComputerLeftMouseDownConfig

class BetaComputerToolsetConfigs(BaseModel):
    """
    Per-member configuration for ``computer_toolset_20260801``: one
    optional field per member tool, keyed by the member name — the same
    name the member's ``tool_use`` blocks carry. Every member is an
    accepted key, and a member's defaults apply wherever its key is
    absent. Unknown keys are rejected: the field set is this toolset
    version's complete member set.
    """
    cursor_position: Optional[BetaComputerCursorPositionConfig] = None
    double_click: Optional[BetaComputerDoubleClickConfig] = None
    hold_key: Optional[BetaComputerHoldKeyConfig] = None
    key: Optional[BetaComputerKeyConfig] = None
    left_click: Optional[BetaComputerLeftClickConfig] = None
    left_click_drag: Optional[BetaComputerLeftClickDragConfig] = None
    left_mouse_down: Optional[BetaComputerLeftMouseDownConfig] = None
    left_mouse_up: Optional[BetaComputerLeftMouseUpConfig] = None
    middle_click: Optional[BetaComputerMiddleClickConfig] = None
    mouse_move: Optional[BetaComputerMouseMoveConfig] = None
    right_click: Optional[BetaComputerRightClickConfig] = None
    screenshot: Optional[BetaComputerScreenshotConfig] = None
    scroll: Optional[BetaComputerScrollConfig] = None
    triple_click: Optional[BetaComputerTripleClickConfig] = None
    type: Optional[BetaComputerTypeConfig] = None
    wait: Optional[BetaComputerWaitConfig] = None
    zoom: Optional[BetaComputerZoomConfig] = None
