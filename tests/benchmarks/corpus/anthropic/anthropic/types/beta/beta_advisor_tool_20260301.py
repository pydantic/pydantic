
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import List, Optional
from typing_extensions import Literal
from ..model import Model
from ..._models import BaseModel
from .beta_cache_control_ephemeral import BetaCacheControlEphemeral

class BetaAdvisorTool20260301(BaseModel):
    model: Model
    name: Literal['advisor']
    type: Literal['advisor_20260301']
    allowed_callers: Optional[List[Literal['direct', 'code_execution_20250825', 'code_execution_20260120', 'code_execution_20260521']]] = None
    cache_control: Optional[BetaCacheControlEphemeral] = None
    caching: Optional[BetaCacheControlEphemeral] = None
    defer_loading: Optional[bool] = None
    max_tokens: Optional[int] = None
    max_uses: Optional[int] = None
    strict: Optional[bool] = None
