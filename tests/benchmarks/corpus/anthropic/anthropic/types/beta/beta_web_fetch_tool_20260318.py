
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import List, Optional
from typing_extensions import Literal
from ..._models import BaseModel
from .beta_web_fetch_url_sources import BetaWebFetchURLSources
from .beta_citations_config_param import BetaCitationsConfigParam
from .beta_cache_control_ephemeral import BetaCacheControlEphemeral

class BetaWebFetchTool20260318(BaseModel):
    name: Literal['web_fetch']
    type: Literal['web_fetch_20260318']
    allowed_callers: Optional[List[Literal['direct', 'code_execution_20250825', 'code_execution_20260120', 'code_execution_20260521']]] = None
    allowed_domains: Optional[List[str]] = None
    blocked_domains: Optional[List[str]] = None
    cache_control: Optional[BetaCacheControlEphemeral] = None
    citations: Optional[BetaCitationsConfigParam] = None
    defer_loading: Optional[bool] = None
    max_content_tokens: Optional[int] = None
    max_uses: Optional[int] = None
    response_inclusion: Optional[Literal['full', 'excluded']] = None
    strict: Optional[bool] = None
    url_sources: Optional[BetaWebFetchURLSources] = None
    use_cache: Optional[bool] = None
