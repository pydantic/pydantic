
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import List, Optional
from typing_extensions import Literal
from ..._models import BaseModel
from .beta_user_location import BetaUserLocation
from .beta_cache_control_ephemeral import BetaCacheControlEphemeral

class BetaWebSearchTool20260318(BaseModel):
    name: Literal['web_search']
    type: Literal['web_search_20260318']
    allowed_callers: Optional[List[Literal['direct', 'code_execution_20250825', 'code_execution_20260120', 'code_execution_20260521']]] = None
    allowed_domains: Optional[List[str]] = None
    blocked_domains: Optional[List[str]] = None
    cache_control: Optional[BetaCacheControlEphemeral] = None
    defer_loading: Optional[bool] = None
    max_uses: Optional[int] = None
    response_inclusion: Optional[Literal['full', 'excluded']] = None
    strict: Optional[bool] = None
    user_location: Optional[BetaUserLocation] = None
