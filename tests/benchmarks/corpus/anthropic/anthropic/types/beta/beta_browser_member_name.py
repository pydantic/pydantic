
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal, TypeAlias
BetaBrowserMemberName: TypeAlias = Literal['navigate', 'list_tabs', 'new_tab', 'switch_tab', 'close_tab', 'read_page', 'get_page_text', 'read_console', 'read_network', 'find', 'form_input', 'file_upload', 'scroll_to', 'screenshot', 'zoom', 'left_click', 'right_click', 'middle_click', 'double_click', 'triple_click', 'hover', 'left_click_drag', 'left_mouse_down', 'left_mouse_up', 'mouse_move', 'scroll', 'type', 'key', 'hold_key', 'wait', 'javascript_exec']
