
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import List, Optional
from typing_extensions import Literal
from ..._models import BaseModel
from .beta_cache_control_ephemeral import BetaCacheControlEphemeral

class BetaToolSearchToolRegex20251119(BaseModel):
    name: Literal['tool_search_tool_regex']
    type: Literal['tool_search_tool_regex_20251119', 'tool_search_tool_regex']
    allowed_callers: Optional[List[Literal['direct', 'code_execution_20250825', 'code_execution_20260120', 'code_execution_20260521']]] = None
    cache_control: Optional[BetaCacheControlEphemeral] = None
    defer_loading: Optional[bool] = None
    strict: Optional[bool] = None
